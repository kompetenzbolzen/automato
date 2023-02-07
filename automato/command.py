from . import transport

'''
Implementations of Command:

MUST implement:
  execute(self, **kwargs)

CAN implement:
  __init__(self, transport)

SHOULDNT implement:
  ./.
'''
class Command:
    def __init__(self, transport: transport.Transport):
        self._transport = transport

    def execute(self, **kwargs):
        raise NotImplemented

class NotifyCommand(Command):
    def __init__(self, transport: transport.SshTransport):
        self._transport = transport

    def execute(self, msg: str):
        self._transport.execHandleStderror(f'notify-send "{msg}"')
