from automato import transport

import logging

import binascii
import socket

logger = logging.getLogger(__name__)
'''
Implementations of Command:

MUST implement:
  execute(self, **kwargs)

CAN implement:
  _init(self, transport, ...)

SHOULDNT implement:
  __init__(self, endpoint_info: dict, **kwargs):
'''
class Command:
    # TODO do we need config for commands?
    def __init__(self, endpoint_info: dict, **kwargs):
        self._endpoint_info = endpoint_info
        self._init(**kwargs)

    def _init(self, transport: transport.Transport):
        self._transport = transport

    def execute(self, **kwargs):
        raise NotImplemented

class NotifyCommand(Command):
    def _init(self, transport: transport.SshTransport):
        self._transport = transport

    def execute(self, msg: str):
        self._transport.execHandleStderror(f'notify-send "{msg}"')

'''
WakeOnLanCommand sends a WOL magic packet to wake a device.

Transport: MetaDataTransport with attribute 'mac' set to the devices'
MAC Address in the standard XX:XX:XX:XX:XX:XX format.
'''
class WakeOnLanCommand(Command):
    def _init(self):
        if not 'mac' in self._endpoint_info:
            logger.error('MAC Address is not set in endpoint info.')

        self._mac = self._endpoint_info.get('mac', "00:00:00:00:00")

    def execute(self):
        mac_bytes = b''
        try:
            mac_bytes = binascii.unhexlify(self._mac.replace(':',''))
        except binascii.Error:
            logger.error(f'MAC Address "{self._mac}" failed to parse to binary')
            return

        if len(mac_bytes) != 6:
            logger.error(f'MAC Address "{self._mac}" is malformed')
            return

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        magic = b'\xff' * 6 + mac_bytes * 16
        s.sendto(magic, ('<broadcast>', 7))

        logger.debug(f'Sent magic packet to {self._mac}')
