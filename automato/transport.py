import paramiko

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
  __init__(self, <other settings you might need>)
  isConnected(self) -> bool

SHOULDNT implement:
  ./.
'''
class Transport:
    CONNECTION = HOLD
    #CONNECTION = THROWAWAY

    def __init__(self):
        self._connected = False

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

class SshTransport(Transport):
    CONNECTION=HOLD

    def __init__(self, hostname: str, port=22,  username='root', password = None, id_file = None, allow_agent=False):
        super().__init__()
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
        self._client.connect(self._hostname, port=self._port, username=self._username, password=self._password, key_filename=self._id_file, allow_agent=self._allow_agent)

        self._connected = True

    # return(str: stdout, str: stderr, int: retcode)
    def exec(self, command: str):
        if not self._connected:
            raise Exception('Not connected')

        output = self._client.exec_command(command, timeout=5)

        retcode = output[1].channel.recv_exit_status()
        return (output[1].read().strip(), output[2].read().strip(), retcode)

    def execHandleStderror(self, command: str):
        out = self.exec(command)

        if out[2] != 0:
            raise Exception(f'Command returned error {out[2]}: {out[1]}')

        return out[0]

    def readFile(self, path: str):
        return self.execHandleStderror(f'cat "{path}"')

    def disconnect(self):
        if self._connected:
            self._client.close()

        self._connected = False
        self._client = None
