from typing import Dict
from pyparsing import alphanums, alphas, printables, pyparsing_common, pyparsing_common, Word, infix_notation, CaselessKeyword, opAssoc, ParserElement
import logging
import time

from . import endpoint
from . import misc

'''
Implementations of Trigger:

MUST implement:
  _evaluate(self, action: str) -> bool
    evaluates the instace for action given by 'action'.
    Provided configuration is stored in self._instances[action]['args']

CAN implement:
  _addInstance(self, action: str)
    Called afer 'action' was added.

SHOULDNT implement:
  evaluate(self, action: str) -> bool
    Only calls _evaluate(), if no check was performed in configured interval,
    otherwise returns cached result
  addInstance(self, action:str, interval=30, **kwargs)
'''
class Trigger:
    NEEDS_CONTEXT = False

    @staticmethod
    def create(classname: str, **kwargs):
        return misc.import_class(classname)(**kwargs)

    def __init__(self):
        self._instances = {}

    def _addInstance(self, action: str):
        pass

    def addInstance(self, action: str, interval: int=30, **kwargs):
        self._instances[action] = {'lastupdate':0,'interval':interval,'last':False,'args':kwargs}
        self._addInstance(action)
        logging.debug(f'Trigger: Action "{action}" registered.')

    def _evaluate(self, action: str) -> bool:
        raise NotImplemented

    def _shouldReevaluate(self, action: str) -> bool:
        return time.time() - self._instances[action]['lastupdate'] > self._instances[action]['interval']

    def evaluate(self, action: str) -> bool:
        if action not in self._instances:
            logging.error(f'Trigger: Action "{action}" was not found. Evaluating to False.')
            return False

        if self._shouldReevaluate(action):
            logging.debug(f'Re-evaluating trigger condition for action "{action}"')
            result =  self._evaluate(action)

            self._instances[action]['last'] = result
            self._instances[action]['lastupdate'] = time.time()
            return result

        return self._instances[action]['last']

'''
```yaml
conditional:
  class: trigger.Conditional
---
- conditional:
  interval: 30
  when:
    - host1.user.bob > 0
```
'''
class ConditionalTrigger(Trigger):
    NEEDS_CONTEXT = True

    def __init__(self, endpoints: Dict[str, endpoint.Endpoint]):
        super().__init__()

        self._endpoints = endpoints
        self._setup_parser()

    def _setup_parser(self):
        ParserElement.enable_packrat()

        boolean = CaselessKeyword('True').setParseAction(lambda x: True) | CaselessKeyword('False').setParseAction(lambda x: False)
        integer = pyparsing_common.integer
        variable = Word(alphanums + '.').setParseAction(self._parseVariable)
        operand = boolean | integer | variable

        self._parser = infix_notation(
                operand,
                [
                    ('not', 1, opAssoc.RIGHT, lambda a: not a[0][1]),
                    ('and', 2, opAssoc.LEFT, lambda a: a[0][0] and a[0][2]),
                    ('or', 2, opAssoc.LEFT, lambda a: a[0][0] or a[0][2]),
                    ('==', 2, opAssoc.LEFT, lambda a: a[0][0] == a[0][2]),
                    ('>', 2, opAssoc.LEFT, lambda a: a[0][0] > a[0][2]),
                    ('>=', 2, opAssoc.LEFT, lambda a: a[0][0] >= a[0][2]),
                    ('<', 2, opAssoc.LEFT, lambda a: a[0][0] < a[0][2]),
                    ('<=', 2, opAssoc.LEFT, lambda a: a[0][0] <= a[0][2]),
                    ('+', 2, opAssoc.LEFT, lambda a: a[0][0] + a[0][2]),
                    ('-', 2, opAssoc.LEFT, lambda a: a[0][0] - a[0][2]),
                    ('*', 2, opAssoc.LEFT, lambda a: a[0][0] * a[0][2]),
                    ('/', 2, opAssoc.LEFT, lambda a: a[0][0] / a[0][2]),
                ]
            )

    def _parseVariable(self, var):
        logging.debug(f'Looking up variable "{var[0]}"')
        endpoint, key = var[0].split('.',1)

        if not endpoint in self._endpoints:
            logging.error(f'Parser: Endpoint "{endpoint}" not found')
            return None

        return self._endpoints[endpoint].getState(key)

    def _evaluate(self, action: str) -> bool:
        return all(self._parser.parse_string(str(s)) for s in self._instances[action]['args']['when'])

