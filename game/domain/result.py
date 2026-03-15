from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class SimulationResult:
    winner: str
    players: List[str]
    total_rounds: int
    end_reason: str

    def to_dict(self) -> dict:
        return {
            'vencedor': self.winner,
            'jogadores': self.players,
        }
