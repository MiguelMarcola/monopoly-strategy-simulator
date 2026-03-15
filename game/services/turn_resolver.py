from copy import deepcopy
from typing import Callable, List, Optional, Tuple

from game.domain.board import move
from game.domain.constants import BOARD_SIZE
from game.domain.events import (
    DiceRolled,
    GameEvent,
    LapCompleted,
    PlayerBankrupted,
    PropertyBought,
    PropertyNotBought,
    PropertiesReleased,
    RentPaid,
)
from game.domain.player import Player
from game.domain.property import Property
from game.domain.result import SimulationResult
from game.domain.strategies import (
    CautiousStrategy,
    DemandingStrategy,
    ImpulsiveStrategy,
    RandomStrategy,
)
from game.services.dice import Dice

EventEmitter = Callable[[GameEvent], None]
Strategy = type

PLAYER_TYPES: List[Tuple[str, Strategy]] = [
    ('impulsivo', ImpulsiveStrategy),
    ('exigente', DemandingStrategy),
    ('cauteloso', CautiousStrategy),
    ('aleatorio', RandomStrategy),
]


class TurnResolver:
    def __init__(
        self,
        dice: Dice,
        emit: EventEmitter,
        strategies: List[Tuple[str, Strategy]],
    ):
        self.dice = dice
        self.emit = emit
        self.strategies = [(name, strat()) for name, strat in strategies]

    def resolve(
        self,
        player: Player,
        properties: List[Property],
        players: List[Player],
        round_num: int,
    ) -> Tuple[Player, List[Property]]:
        dice_value = self._roll_dice()
        move_result = move(player.position, dice_value)

        if move_result.completed_lap:
            player = player.credit(move_result.lap_bonus)
            self.emit(LapCompleted(round_num, player.name, move_result.lap_bonus, player.balance))

        player = player.move_to(move_result.new_position)
        from_position = (move_result.new_position - dice_value) % BOARD_SIZE
        self.emit(DiceRolled(
            round_num, player.name, dice_value,
            from_position,
            move_result.new_position,
            player.balance,
        ))

        property_at = properties[move_result.new_position]

        if property_at.is_available():
            player, properties = self._resolve_purchase(player, property_at, properties, players, round_num)
        elif property_at.requires_rent_from(player.name):
            player, properties = self._resolve_rent(player, property_at, players, properties, round_num)

        if player.is_bankrupt():
            self.emit(PlayerBankrupted(round_num, player.name, player.balance))

        return player, properties

    def _roll_dice(self) -> int:
        return self.dice.roll()

    def _resolve_purchase(
        self,
        player: Player,
        property_at: Property,
        properties: List[Property],
        players: List[Player],
        round_num: int,
    ) -> Tuple[Player, List[Property]]:
        _, strategy = self.strategies[player.turn_order]
        if strategy.should_buy(player, property_at):
            player = player.debit(property_at.sale_cost)
            new_prop = property_at.with_owner(player.name)
            new_properties = properties.copy()
            new_properties[property_at.position] = new_prop
            self.emit(PropertyBought(
                round_num, player.name, property_at.position,
                property_at.sale_cost, player.balance,
            ))
            return player, new_properties
        reason = 'comportamento' if player.can_afford(property_at.sale_cost) else 'saldo_insuficiente'
        self.emit(PropertyNotBought(
            round_num, player.name, property_at.position,
            property_at.sale_cost, reason,
        ))
        return player, properties

    def _resolve_rent(
        self,
        player: Player,
        property_at: Property,
        players: List[Player],
        properties: List[Property],
        round_num: int,
    ) -> Tuple[Player, List[Property]]:
        player = player.debit(property_at.rent_value)
        owner_idx = next(i for i, p in enumerate(players) if p.name == property_at.owner)
        owner = players[owner_idx].credit(property_at.rent_value)
        players[owner_idx] = owner
        self.emit(RentPaid(
            round_num, player.name, property_at.owner,
            property_at.position, property_at.rent_value, player.balance,
        ))
        return player, properties


def release_bankrupt_properties(
    players: List[Player],
    properties: List[Property],
    emit: EventEmitter,
) -> List[Property]:
    bankrupt_names = {p.name for p in players if p.is_bankrupt()}
    if not bankrupt_names:
        return properties
    new_properties = []
    for prop in properties:
        if prop.owner and prop.owner in bankrupt_names:
            new_properties.append(prop.without_owner())
            emit(PropertiesReleased(prop.owner, prop.position))
        else:
            new_properties.append(prop)
    return new_properties


def determine_winner(players: List[Player]) -> Tuple[str, List[str]]:
    sorted_players = sorted(players, key=lambda p: (-p.balance, p.turn_order))
    return sorted_players[0].name, [p.name for p in sorted_players]
