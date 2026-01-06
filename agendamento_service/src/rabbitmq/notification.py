from dataclasses import dataclass, field
from datetime import datetime, timezone
import json

@dataclass
class Notification:
    user_id: int
    agendamento_id: int
    novo_status: str
    mensagem: str
    origem: str = "AGENDAMENTO"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_json(self) -> str:
        return json.dumps(self.__dict__)