import time
import logging
logger = logging.getLogger(__name__)

from . import transport

'''
Implementations of State:

MUST implement:
  _collect(self)

CAN implement:
  _get(self, key: str)
  init(self, [transport], <other options you might need>)

SHOULDNT implement:
  get(self, key)
  collect(self)
  __init__(self, endpoint_info: dict, ttl: int = 30, **kwargs)

Data is stored in self._data as a dictionary.
By default, _get(key) retrieves the returns self._data[key].
This behaviour can be overridden by implementing a own _get().

If using the default _get(), _collect() has to store data in
the self._data dictionary. If an own _get() is implemented,
this does not need to be the case.
'''
class State:
    # TODO set default TTL in child classes
    def __init__(self, endpoint_info: dict, ttl: int = 30, **kwargs):
        self._ttl = ttl
        self._endpoint_info = endpoint_info

        self._data = {}
        self._last_collected = 0

        self._init(**kwargs)

    def _init(self):
        pass

    def _collect(self):
        raise NotImplemented

    def _get(self, key: str):
        if key not in self._data:
            logger.error(f'Data key {key} was not found.')
            return None

        return self._data[key]

    def _shouldCollect(self):
        return time.time() - self._last_collected > self._ttl

    def get(self, key: str):
        if self._shouldCollect():
            logger.debug(f'Cached value for "{key}" is too old. refreshing.')
            self.collect()
        else:
            logger.debug(f'Using cached value for "{key}".')


        return self._get(key)

    # Force datacollection. not really needed
    def collect(self):
        self._collect()
        self._last_collected = time.time()

class UserSessionState(State):
    def _init(self, transport: transport.SshTransport):
        self._transport = transport

    def _get(self, key: str):
        if key not in self._data:
            return 0

        return self._data[key]

    def _collect(self):
        data = self._transport.execHandleStderror('who').decode('utf-8')
        # TODO error handling
        lines = data.split('\n')

        self._data = {}

        for l in lines:
            name, _ = l.split(' ', 1)

            logger.debug(f'Found user session {name}')

            if name not in self._data:
                self._data[name] = 0

            self._data[name] += 1

class LinuxMemoryState(State):
    def _init(self, transport: transport.SshTransport):
        self._transport = transport

    def _collect(self):
        mem_data = self._transport.execHandleStderror('cat /proc/meminfo').decode('utf-8')

        # TODO We prbly don't wan't raw values. Process them!
        self._data['mem'] = {}
        for l in mem_data.splitlines():
            arr = l.split()
            key = arr[0].strip(':')
            val = arr[1]

            self._data['mem'][key] = val

            logger.debug(f'Memory: {key} = {val}')

class LinuxLoadState(State):
    def _init(self, transport: transport.SshTransport):
        self._transport = transport

    def _collect(self):
        load_raw = self._transport.execHandleStderror('cat /proc/loadavg').decode('utf-8')

        data = load_raw.split(None,4)

        self._data = {}

        self._data['1'] = data[0]
        self._data['5'] = data[1]
        self._data['15'] = data[2]
