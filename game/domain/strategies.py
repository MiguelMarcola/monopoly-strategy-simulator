from abc import ABC, abstractmethod
import random

from game.domain.constants import (
    CAUTIOUS_MIN_RESERVE,
    DEMANDING_MIN_RENT,
    RANDOM_BUY_PROBABILITY,
)
from game.domain.player import Player
from game.domain.property import Property


class BuyStrategy(ABC):
    @abstractmethod
    def should_buy(self, player: Player, property_obj: Property) -> bool:
        pass


class ImpulsiveStrategy(BuyStrategy):
    def should_buy(self, player: Player, property_obj: Property) -> bool:
        return property_obj.can_be_bought_by(player)


class DemandingStrategy(BuyStrategy):
    def should_buy(self, player: Player, property_obj: Property) -> bool:
        return (
            property_obj.can_be_bought_by(player)
            and property_obj.rent_value > DEMANDING_MIN_RENT
        )


class CautiousStrategy(BuyStrategy):
    def should_buy(self, player: Player, property_obj: Property) -> bool:
        if not property_obj.can_be_bought_by(player):
            return False
        balance_after = player.balance - property_obj.sale_cost
        return balance_after >= CAUTIOUS_MIN_RESERVE


class RandomStrategy(BuyStrategy):
    def should_buy(self, player: Player, property_obj: Property) -> bool:
        return (
            property_obj.can_be_bought_by(player)
            and random.random() < RANDOM_BUY_PROBABILITY
        )
