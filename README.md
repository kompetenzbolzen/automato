# automato

## Paradigm
___

#### Endpoint

Object to group *States*, *Commands* and *Transports*.
Endpoints can be seen as a *Transport Domain*, commands and states can only use the ones of their endpoint.
In most cases this would be a logical host, like a Raspberry, PC or VM.

#### State

A (numeric) value, or set of values, describing the current state of an *endpoint*.
They are collected on demand and cached for a specific time set by the `ttl` parameter.
A State is addressed via `<endpoint>.<state>`,
some states allow passing of keys to select from multiple values by a dot followed by the key: `<endpoint>.<state>.<key>`


#### Command

A way of manipulating an *endpoint*.
A State is addressed via `<endpoint>.<command>` and can accept additional arguments upon invocation.


#### Transport

Communication channel to the *endpoint* used by *commands* and *states*.
A transport can only be used by *commands* and *states* of its *endpoint* and thus is just referenced by its name.

#### Trigger

regularily checked conditions used to trigger *actions*.
Triggers are re-evaluated in an interval set by the `interval` parameter.
*Actions* hold instances of triggers, which can have their own settings,
but still inherit the globally set ones.


#### Action

An *If-This-Then-That* style set of *triggers* and *commands*.
If all *triggers* are in a triggered state, the commands are executed.
If `repeat` is `False`, the evaluation must cycle through `False` to run again.
`cooldown` specifies the time in seconds the action will wait after running again,
even if conditions are met.
Both `repeat` and `cooldown` are optional and their defaults are `True` and `0`.


## Configuration
___

automato is configured in three `yml`-files

`endpoints.yml`
```yaml
host1:
  transports:
    ssh:
      class: automato.transport.SshTransport
      hostname: 'localhost'
      username: 'jonas'
  commands:
    notify:
      class: automato.command.NotifyCommand
      transport: ssh
  states:
    user:
      class: automato.state.UserSessionState
      transport: ssh
      ttl: 30
```

`triggers.yml`
```yaml
conditional:
  class: automato.trigger.ConditionalTrigger
```

`actions.yml`
```yaml
send-hello:
  repeat: False
  cooldown: 30
  trigger:
    - conditional:
        interval: 30
        when:
          - host1.user.jonas > 0
          - True
  then:
    - host1.notify:
        msg: Hello
    - host1.notify:
        msg: World!
```
