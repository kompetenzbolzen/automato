import logging
import requests

from automato.transport import Transport, THROWAWAY

logger = logging.getLogger(__name__)

'''
HttpTransport

REQUIRED ARGUMENTS
    address: Base Address of endpoint
OPTIONAL ARGUMENTS
    user: Username for HTTP basic auth.
    password: Password for HTTP basic auth
    headers: Dict for headers to add in every connection
    user_agent: Change the user agent form the default requests
'''
class HttpTransport(Transport):
    CONNECTION = THROWAWAY

    def _init(self, address:str,
              user:[None,str] = None, password:[None,str] = None,
              headers:[None,dict] = None, user_agent:[None,str] = None,
              validation_path: str = '/', timeout:int = 30):
        self._address = address
        self._user = user
        self._password = password
        self._headers = headers
        self._user_agent = user_agent
        self._validation_path = '/'
        self._timeout = timeout

    def check(self):
        # TODO Here we could maybe also perform a more complex login
        # with Cookies?

        ret = self.request('HEAD', self._validation_path)
        logger.debug(f'{self._validation_path} checked {ret.ok} with code {ret.status_code}')

        return ret.ok


    def request(self, method:str, path:str, headers:[None,dict] = None,
                 data = None, params:[None,str] = None):
        full_path = self._address.rstrip('/') + '/' + path.lstrip('/')
        logger.debug(f'requested {method} for {full_path}')

        all_headers = headers

        if self._headers is not None:
            if headers is not None:
                all_headers = self._headers | headers
            else:
                all_headers = self._headers

        # TODO maybe pass **kwargs here?
        try:
            req = requests.request(method, full_path, headers=all_headers,
                                   data=data, params=params, timeout=self._timeout)
            return req
        except requests.RequestException as e:
            logger.error(f'An exception occured in {method} for {full_path}: {e}')
            #FIXME We need better error handling
            return None


    def get(self, **kwargs):
        return self.request('GET', **kwargs)
    def head(self, **kwargs):
        return self.request('HEAD', **kwargs)
    def put(self, **kwargs):
        return self.request('PUT', **kwargs)
    def post(self, **kwargs):
        return self.request('POST', **kwargs)
    def patch(self, **kwargs):
        return self.request('PATCH', **kwargs)
    def delete(self, **kwargs):
        return self.request('DELETE', **kwargs)
