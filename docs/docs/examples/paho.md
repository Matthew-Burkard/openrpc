---
id: Paho
slug: /examples/sanic
sidebar_position: 4
---

# Paho

The following is an example of a [Paho](https://eclipse.dev/paho/) server exposing an
OpenRPC server over MQTT.

```python
import json
import time

import paho.mqtt.client as mqtt
from openrpc import RPCServer

rpc = RPCServer(title="DemoServer", version="1.0.0")
topic = "/api/v1"
client = mqtt.Client("MQTTClient")


@rpc.method()
async def add(a: int, b: int) -> int:
    return a + b


def on_message(_client: mqtt.Client, _userdata, message: mqtt.MQTTMessage) -> None:
    """Process RPC requests and reply."""
    json_rpc_response = rpc.process_request(message.payload.decode('utf-8'))
    id_ = json.loads(message.payload).get("id")
    if id_ is not None:
        client.publish(f"{topic}/responses/{id_}", json_rpc_response)


if __name__ == "__main__":
    client.connect("127.0.0.1")
    client.loop_start()
    client.subscribe(topic)
    client.on_message = on_message
    # Run forever.
    while True:
        time.sleep(1.0)
```
