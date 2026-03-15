from dataclasses import dataclass
from typing import List, Tuple

from game.domain.constants import BOARD_SIZE, LAP_BONUS
from game.domain.property import Property


@dataclass(frozen=True)
class MoveResult:
    new_position: int
    completed_lap: bool
    lap_bonus: int


def create_default_board() -> List[Property]:
    return [
        Property(0, 80, 20),
        Property(1, 100, 30),
        Property(2, 120, 40),
        Property(3, 140, 50),
        Property(4, 160, 60),
        Property(5, 180, 70),
        Property(6, 200, 80),
        Property(7, 220, 90),
        Property(8, 240, 100),
        Property(9, 260, 110),
        Property(10, 280, 120),
        Property(11, 300, 130),
        Property(12, 320, 140),
        Property(13, 350, 160),
        Property(14, 400, 200),
        Property(15, 450, 250),
        Property(16, 500, 300),
        Property(17, 550, 350),
        Property(18, 600, 400),
        Property(19, 1000, 500),
    ]


DEFAULT_BOARD = create_default_board()


def move(current_position: int, dice_value: int) -> MoveResult:
    new_position = (current_position + dice_value) % BOARD_SIZE
    completed_lap = new_position < current_position
    lap_bonus = LAP_BONUS if completed_lap else 0
    return MoveResult(
        new_position=new_position,
        completed_lap=completed_lap,
        lap_bonus=lap_bonus,
    )
