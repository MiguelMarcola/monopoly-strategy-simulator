from dataclasses import dataclass
from typing import Optional

from game.domain.player import Player


@dataclass(frozen=True)
class Property:
    position: int
    sale_cost: int
    rent_value: int
    owner: Optional[str] = None

    def is_available(self) -> bool:
        return self.owner is None

    def is_owned_by(self, player_name: str) -> bool:
        return self.owner == player_name

    def requires_rent_from(self, player_name: str) -> bool:
        return self.owner is not None and self.owner != player_name

    def can_be_bought_by(self, player: Player) -> bool:
        return self.is_available() and player.can_afford(self.sale_cost)

    def with_owner(self, name: str) -> 'Property':
        return Property(
            position=self.position,
            sale_cost=self.sale_cost,
            rent_value=self.rent_value,
            owner=name,
        )

    def without_owner(self) -> 'Property':
        return Property(
            position=self.position,
            sale_cost=self.sale_cost,
            rent_value=self.rent_value,
            owner=None,
        )
