import logging
logger = logging.getLogger(__name__)

from automato import transport

def import_class(cl):
    d = cl.rfind(".")
    classname = cl[d+1:len(cl)]
    m = __import__(cl[0:d], globals(), locals(), [classname])
    return getattr(m, classname)

    # Master object
class Endpoint:
    def __init__(self, name: str, config: dict):
        transports = {}
        commands = {}
        states = {}

        endpoint_info = config.get('info', {})

        # sweet mother of jesus, you are ugly
        for tp_key in config['transports']:
            tp_cfg = config['transports'][tp_key]
            logger.debug(f'loading transport "{tp_key}"')

            # TODO Handle failure
            tp_class = import_class(tp_cfg['class'])
            del tp_cfg['class']

            transports[tp_key] = tp_class(endpoint_info, **tp_cfg)

        for cmd_key in config['commands']:
            cmd_cfg = config['commands'][cmd_key]
            logger.debug(f'loading command "{cmd_key}"')

            # TODO Handle failure
            cmd_class = import_class(cmd_cfg['class'])
            del cmd_cfg['class']

            if 'transport' in cmd_cfg:
                if cmd_cfg['transport'] not in transports:
                    # TODO should we be lenient with errors?
                    logger.error(f'transport "{cmd_cfg["transport"]}" for command "{cmd_key}" was not found.')
                    continue

                tp = transports[cmd_cfg['transport']]
                del cmd_cfg['transport']
                cmd_cfg['transport'] = tp

            commands[cmd_key] = cmd_class(endpoint_info, **cmd_cfg)

        # you look familiar
        for stt_key in config['states']:
            stt_cfg = config['states'][stt_key]
            logger.debug(f'loading state "{stt_key}"')

            # TODO Handle failure
            stt_class = import_class(stt_cfg['class'])
            del stt_cfg['class']

            if stt_cfg['transport'] not in transports:
                # TODO should we be lenient with errors?
                logger.error(f'transport "{stt_cfg["transport"]}" for command "{stt_key}" was not found.')
                continue

            if 'transport' in stt_cfg:
                tp = transports[stt_cfg['transport']]
                del stt_cfg['transport']
                stt_cfg['transport'] = tp

            states[stt_key] = stt_class(endpoint_info, **stt_cfg)

        # TODO How does the init step look like? Do it here?
        # transports prbly need to be connected here

        self._name = name
        self._transports = transports
        self._commands = commands
        self._states = states

    def connectTransport(self):
        for k in self._transports:
            if   self._transports[k].CONNECTION == transport.HOLD:
                self._transports[k].connect()
            elif self._transports[k].CONNECTION == transport.THROWAWAY:
                self._transports[k].check()
            else:
                logger.error(f'"{self._transports[k].CONNECTION}" is an unknown connection type in transport "{k}"')

    # forces a recollect of all states. should not be needed, states should
    # handle that themselves via TTL
    # we shouldn't need it
    #def collectState(self):
    #    # TODO we need a interface here
    #    for k in self._states:
    #        self._states[k].collect()

    # Format: <state>.<key>
    def getState(self, state_key: str):
        state, key = state_key.split('.', 1)

        if state not in self._states:
            logger.error(f'State "{state}" was not found for "{self._name}"')
            return None

        return self._states[state].get(key)


    def executeCommand(self, cmd: str, **kwargs):
        if cmd not in self._commands:
            logger.error(f'Command "{cmd}" is not defined for "{self._name}"')
            #raise Exception(f'Command "{cmd}" is not defined for "{self._name}"')

        self._commands[cmd].execute(**kwargs)
