from typing import Dict
import logging

from . import endpoint
from . import trigger

class Action:
    # TODO: Cooldown, wait fot state change, repeat, etc?
    def __init__(self, name: str, config: dict, endpoints: Dict[str, endpoint.Endpoint], triggers: Dict[str, trigger.Trigger]):
        self._name = name
        self._trigger_cfg = config['trigger']
        self._then_cfg = config['then']

        self._endpoints = endpoints
        self._triggers = triggers

        self._configured_trigger_keys = []

        self._setup_triggers()

    def _setup_triggers(self):
        for trg_list_item in self._trigger_cfg:
            if len(trg_list_item.keys()) != 1:
                logging.error(f'Action "{self._name}" encountered error while adding trigger "{trg_list_item}"')
                raise Exception

            trg_key = list(trg_list_item.keys())[0]
            trg_config = trg_list_item[trg_key]

            if not trg_key in self._triggers:
                logging.error(f'Action "{self._name}": Trigger "{trg_key}" is not configured.')
                raise Exception

            self._configured_trigger_keys.append(trg_key)
            self._triggers[trg_key].addInstance(self._name, **trg_config)
            logging.debug(f'Action "{self._name}" was registered with "{trg_key}"')


    def execute(self):
        if not all([self._triggers[b].evaluate(self._name) for b in self._configured_trigger_keys]):
            logging.debug(f'Action "{self._name}" will not execute. Conditions not met.')
            return

        logging.info(f'Executing Action "{self._name}". Conditions are met.')

        for then_item in self._then_cfg:
            if len(then_item.keys()) != 1:
                logging.error(f'Action "{self._name}" encountered error while executing command "{then_item}"')
                raise Exception

            cmd_key = list(then_item.keys())[0]
            cmd_config = then_item[cmd_key]

            logging.info(f'Executing command "{cmd_key}"')
            endpoint, command = cmd_key.split('.', 1)
            self._endpoints[endpoint].executeCommand(command, **cmd_config)


