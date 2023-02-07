import time
import logging

import transport

'''
Implementations of State:

MUST implement:
  _collect(self)

CAN implement:
  _get(self, key: str)

SHOULDNT implement:
  get(self, key)
  collect(self)

Data is stored in self._data as a dictionary.
By default, _get(key) retrieves the returns self._data[key].
This behaviour can be overridden by implementing a own _get().

If using the default _get(), _collect() has to store data in
the self._data dictionary. If an own _get() is implemented,
this does not need to be the case.
'''
class State:
    def __init__(self, transport: transport.Transport, ttl: int = 30):
        self._transport = transport
        self._ttl = ttl

        self._data = {}
        self._last_collected = 0

    def _collect(self):
        raise NotImplemented

    def _get(self, key: str):
        if key not in self._data:
            logging.error(f'Data key {key} was not found.')
            return None

        return self._data[key]

    def _shouldCollect(self):
        return time.time() - self._last_collected > self._ttl

    def get(self, key: str):
        if self._shouldCollect():
            logging.debug(f'Cached value for "{key}" is too old. refreshing.')
            self.collect()
        else:
            logging.debug(f'Using cached value for "{key}".')


        return self._get(key)

    # Force datacollection. not really needed
    def collect(self):
        self._collect()
        self._last_collected = time.time()

class UserSessionState(State):
    def __init__(self, transport: transport.SshTransport, ttl: int = 30):
        super().__init__(transport, ttl)

        # this is not needed. it's here to shut up pylint
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

            logging.debug(f'Found user session {name}')

            if name not in self._data:
                self._data[name] = 0

            self._data[name] += 1
