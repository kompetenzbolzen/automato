#!/usr/bin/env python3

import yaml
import json
import logging
import time

from automato import transport, state, command, endpoint, trigger, misc, action

def main():
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('paramiko').setLevel(logging.WARNING)

    # Use a TypeDict here
    with open('endpoints.yml', 'r') as f:
        endpoint_config = yaml.safe_load(f)

    with open('triggers.yml', 'r') as f:
        trigger_config = yaml.safe_load(f)

    with open('actions.yml', 'r') as f:
        action_config = yaml.safe_load(f)

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

    looptime = 5 # TODO
    while True:
        starttime = time.time()

        for act_key in action_config:
            actions[act_key].execute()

        elapsed = time.time() - starttime
        wait = max(0, looptime - elapsed)
        logging.debug(f'Loop took {elapsed:.2f}s. Waiting {wait:.2f}s before next run.')
        if wait <= 0.1 * looptime:
            logging.warn(f'System seems overloaded. Actions did not run in specified looptime {looptime}s.')

        time.sleep(max(0, looptime - elapsed))



    #for act_key in action_config:
    #    actions[act_key].execute()

    #for act_key in action_config:
    #    actions[act_key].execute()
