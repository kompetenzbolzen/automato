import logging

from automato.transport.http import HttpTransport
from automato.state import State

logger = logging.getLogger(__name__)


class HttpJsonState(State):
    def _init(self, transport: HttpTransport, method: str, path: str,
              json_path: [None,str] = None, **kwargs):

        if json_path is not None:
            logger.warning('Filtering of JSON path requested but not implemented')

        self._transport = transport
        self._path = path
        self._method = method
        self._json_path = json_path
        self._request_args = kwargs

    def _collect(self):
        response = self._transport.request(self._method, self._path,
                                           **self._request_args)
        self._data = response.json()
