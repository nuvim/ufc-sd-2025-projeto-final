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
        return json.dumps({
            "user_id": self.user_id,
            "agendamento_id": self.agendamento_id,
            "novo_status": self.novo_status,
            "mensagem": self.mensagem,
            "origem": self.origem,
            "timestamp": self.timestamp
        })

    @staticmethod
    def from_json(body: str) -> "Notification":
        data = json.loads(body)

        return Notification(
            user_id=data["user_id"],
            agendamento_id=data["agendamento_id"],
            novo_status=data["novo_status"],
            mensagem=data["mensagem"],
            origem=data.get("origem", "AGENDAMENTO"),
            timestamp=data.get("timestamp")
        )
