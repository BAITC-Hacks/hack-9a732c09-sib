from copy import deepcopy
from dataclasses import dataclass, field


@dataclass
class TraceRecorder:
    events: list[dict] = field(default_factory=list)

    def record(self, event: str, payload: dict) -> None:
        self.events.append({"event": event, "payload": deepcopy(payload)})
