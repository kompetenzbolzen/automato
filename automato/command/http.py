import logging
from automato.transport.http import HttpTransport
from automato.command import Command

logger = logging.getLogger(__name__)

class HttpCommand(Command):
    def _init(self, transport: HttpTransport):
        self._transport = transport

    def execute(self, **kwargs):
        req = self._transport.request(**kwargs)
        if not req.ok:
            logger.error(f'HttpCommand request failed with code {req.status_code}')
        else:
            logger.debug(f'HttpCommand exeuted with result {req.ok} Code {req.status_code}')
