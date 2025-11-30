from collections import defaultdict
from aiops_agent.observability.engine import TELEMETRY

class MessageBus:
    def __init__(self): self._queues = defaultdict(list)
    
    def publish(self, sender, recipient, content): 
        self._queues[recipient].append({"from": sender, "msg": content})
        TELEMETRY.log("INFO", "MSG_BUS", f"Message Queued", {"from": sender, "to": recipient})

    def consume(self, recipient): 
        msgs = self._queues.get(recipient, [])
        self._queues[recipient] = []
        return msgs

# Singleton
BUS = MessageBus()
