#!/usr/bin/env python3

import logging
import time
import yaml

from automato import endpoint, misc, action

def load_yaml(path : str):
    # Use a TypeDict here
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def setup():
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s | %(levelname)s | %(name)s - %(message)s',
                        datefmt='%c')

    logging.getLogger('paramiko').setLevel(logging.WARNING)

    endpoint_config = load_yaml('endpoints.yml')
    trigger_config = load_yaml('triggers.yml')
    action_config = load_yaml('actions.yml')

    endpoints = {}
    for ep_key in endpoint_config:
        endpoints[ep_key] = endpoint.Endpoint(ep_key, endpoint_config[ep_key])

    triggers = {}
    for trg_key in trigger_config:
        cls = misc.import_class(trigger_config[trg_key]['class'])
        del trigger_config[trg_key]['class']

        if cls.NEEDS_CONTEXT:
            triggers[trg_key]  = cls(endpoints, **trigger_config[trg_key])
        else:
            triggers[trg_key]  = cls(**trigger_config[trg_key])

    actions = {}
    for act_key in action_config:
        actions[act_key] = action.Action(act_key, action_config[act_key], endpoints, triggers)


    # TODO should we do that in Endpoint.__init__()?
    # TODO We also need better connectivity handling, eg. auto reconnect
    for k in endpoints:
        endpoints[k].connectTransport()

    return actions

def main():
    actions = setup()

    looptime = 5 # TODO
    while True:
        starttime = time.time()

        for act_key in actions:
            actions[act_key].execute()

        elapsed = time.time() - starttime
        wait = max(0, looptime - elapsed)
        logging.debug(f'Loop took {elapsed:.2f}s. Waiting {wait:.2f}s before next run.')
        if wait <= 0.1 * looptime:
            logging.warn(f'System seems overloaded. Actions did not run in specified looptime {looptime}s.')

        time.sleep(max(0, looptime - elapsed))
