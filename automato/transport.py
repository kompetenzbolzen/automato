import paramiko
import logging

from typing import Union

logger = logging.getLogger(__name__)

HOLD = 1
THROWAWAY = 2

'''
Implementations of Transport:

CAN set:
  CONNECTION
    - THROWAWAY signals that every invocation creates a new connection and
      and thus connection management is not needed
    - HOLD indicates a connection is established and held for multiple commands,
      requiring initial connection and final disconnection

MUST implement:
    connect(self), disconnect(self)
      when CONNECTION is set to HOLD
      make sure to set self._connected accordingly.
    check(self)
      when CONNECTION is set to THROWAWAY

    Functions to use the Transport
      it is advisable to specify the used Transport as a type hint in
      the command/state using it to trigger errors on startup,
      rather than at runtime in case of misconfiguration.

CAN implement:
  _init(self, <other settings you might need>)
  isConnected(self) -> bool

SHOULDNT implement:
  __init__(self, endpoint_info: dict, **kwargs)
'''
class Transport:
    CONNECTION = HOLD
    #CONNECTION = THROWAWAY

    def __init__(self, endpoint_info: dict, **kwargs):
        self._endpoint_info = endpoint_info
        self._connected = False
        self._init(**kwargs)

    def _init(self):
        pass

    # Connects to the transport, if CONNECTION == HOLD
    def connect(self):
        raise NotImplemented

    # disconnects to the transport, if CONNECTION == HOLD
    def disconnect(self):
        raise NotImplemented

    # validate that the transport works, if CONNECTION == THROWAWAY
    def check(self):
        raise NotImplemented

    def isConnected(self) -> bool:
        return self._connected

'''
MetaDataTransport holds any data passed to it.
It does not establish any connection and is only used
to store metadata that may be used by commands that do not
require a connection, such as Wake on Lan.
'''
class MetaDataTransport(Transport):
    CONNECTION=THROWAWAY

    def _init(self, **kwargs):
        self._metadata = kwargs

    def __getattr__(self, attr):
        return self._metadata[attr]

    def check(self):
        return True


class SshTransport(Transport):
    CONNECTION=HOLD

    def _init(self, hostname: str, port=22,  username='root', password = None, id_file = None, allow_agent = False):
        self._hostname = hostname
        self._port = port
        self._username = username
        self._password = password
        self._id_file = id_file
        self._allow_agent = allow_agent

        self._client = None

    def connect(self):
        self._client = paramiko.SSHClient()

        # TODO known hosts
        self._client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy)
        try:
            self._client.connect(self._hostname, port=self._port, username=self._username, password=self._password, key_filename=self._id_file, allow_agent=self._allow_agent)
            self._connected = True
        except paramiko.ssh_exception.NoValidConnectionsError as e:
            logger.error(f'Failed to connect to {self._hostname}: {e.errors} ')


    # return(str: stdout, str: stderr, int: retcode)
    def exec(self, command: str):
        if not self._connected:
            # TODO we want a bit smarted connection logic
            logger.error('SSH not connected')
            raise Exception('Not connected')

        output = self._client.exec_command(command, timeout=5)

        retcode = output[1].channel.recv_exit_status()
        return (output[1].read().strip(), output[2].read().strip(), retcode)

    def execHandleStderror(self, command: str):
        out = self.exec(command)

        if out[2] != 0:
            logger.error(f'Command returned error {out[2]}: {out[1]}')
            raise Exception(f'Command returned error {out[2]}: {out[1]}')

        return out[0]

    def readFile(self, path: str):
        return self.execHandleStderror(f'cat "{path}"')

    def disconnect(self):
        if self._connected:
            self._client.close()

        self._connected = False
        self._client = None
