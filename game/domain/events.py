from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class GameEvent:
    pass


@dataclass(frozen=True)
class GameStarted(GameEvent):
    player_order: List[str]
    initial_balance: int


@dataclass(frozen=True)
class DiceRolled(GameEvent):
    round_num: int
    player_name: str
    dice_value: int
    from_position: int
    to_position: int
    balance: int


@dataclass(frozen=True)
class LapCompleted(GameEvent):
    round_num: int
    player_name: str
    bonus: int
    balance: int


@dataclass(frozen=True)
class PropertyBought(GameEvent):
    round_num: int
    player_name: str
    property_position: int
    cost: int
    balance_after: int


@dataclass(frozen=True)
class PropertyNotBought(GameEvent):
    round_num: int
    player_name: str
    property_position: int
    cost: int
    reason: str


@dataclass(frozen=True)
class RentPaid(GameEvent):
    round_num: int
    tenant_name: str
    owner_name: str
    property_position: int
    amount: int
    balance_after: int


@dataclass(frozen=True)
class PlayerBankrupted(GameEvent):
    round_num: int
    player_name: str
    balance: int


@dataclass(frozen=True)
class PropertiesReleased(GameEvent):
    bankrupt_player: str
    property_position: int


@dataclass(frozen=True)
class GameFinished(GameEvent):
    winner: str
    total_rounds: int
    end_reason: str
