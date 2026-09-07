# Messages

The payload schemas, one module per subsystem. All are Pydantic models;
validation happens in the sending process.

```{eval-rst}
.. automodule:: robodog_sdk.msgs.motion
   :members:
   :show-inheritance:
```

```{eval-rst}
.. automodule:: robodog_sdk.msgs.navigation
   :members:
   :show-inheritance:
```

```{eval-rst}
.. automodule:: robodog_sdk.msgs.robot
   :members:
   :show-inheritance:
```

```{eval-rst}
.. automodule:: robodog_sdk.msgs.localization
   :members:
   :show-inheritance:
```

```{eval-rst}
.. automodule:: robodog_sdk.msgs.safety
   :members:
   :show-inheritance:
```

```{eval-rst}
.. automodule:: robodog_sdk.msgs.system_state
   :members:
   :show-inheritance:
```

```{eval-rst}
.. automodule:: robodog_sdk.msgs.input
   :members:
   :show-inheritance:
```

```{eval-rst}
.. automodule:: robodog_sdk.msgs.occupancy
   :members:
   :show-inheritance:
```

## The contract modules

The part every process must agree on besides the payloads themselves: the
key/topic declarations, the robot's capability envelope, and the frame
conventions. [Topics](topics.md) is the primary, human-written reference for
`robodog_sdk.topics`; this section is the generated docstrings for it and its
two companion modules.

```{eval-rst}
.. automodule:: robodog_sdk.topics
   :members:
   :show-inheritance:
```

```{eval-rst}
.. automodule:: robodog_sdk.limits
   :members:
   :show-inheritance:
```

```{eval-rst}
.. automodule:: robodog_sdk.frames
   :members:
   :show-inheritance:
```
