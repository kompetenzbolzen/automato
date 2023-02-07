from . import transport

class Command:
    def __init__(self, transport: transport.Transport):
        raise NotImplemented

    def execute(self, **kwargs):
        raise NotImplemented

class NotifyCommand(Command):
    def __init__(self, transport: transport.SshTransport):
        self._transport = transport

    def execute(self, msg: str, **kwargs):
        self._transport.execHandleStderror(f'notify-send "{msg}"')
