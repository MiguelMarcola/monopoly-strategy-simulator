import random
from copy import deepcopy
from typing import Callable, List, Optional

from game.domain.board import create_default_board
from game.domain.property import Property
from game.domain.constants import INITIAL_BALANCE, MAX_ROUNDS
from game.domain.events import GameEvent, GameFinished, GameStarted
from game.domain.player import Player
from game.domain.result import SimulationResult
from game.domain.strategies import (
    CautiousStrategy,
    DemandingStrategy,
    ImpulsiveStrategy,
    RandomStrategy,
)
from game.services.dice import Dice
from game.services.turn_resolver import (
    TurnResolver,
    determine_winner,
    release_bankrupt_properties,
)

EventEmitter = Callable[[GameEvent], None]


class GameSimulator:
    def __init__(
        self,
        dice: Optional[Dice] = None,
        event_observer: Optional[EventEmitter] = None,
        player_order: Optional[List[int]] = None,
        board: Optional[List[Property]] = None,
    ):
        self.dice = dice or Dice()
        self._emit = event_observer or (lambda e: None)
        self._player_order = player_order
        self._board = board

    def simulate(self) -> SimulationResult:
        players = self._create_players()
        properties = deepcopy(self._board or create_default_board())
        order = self._player_order if self._player_order is not None else list(range(len(players)))
        if self._player_order is None:
            random.shuffle(order)
        ordered_players = [players[i] for i in order]

        self._emit(GameStarted(
            player_order=[p.name for p in ordered_players],
            initial_balance=INITIAL_BALANCE,
        ))

        turn_resolver = TurnResolver(self.dice, self._emit, [
            ('impulsivo', ImpulsiveStrategy),
            ('exigente', DemandingStrategy),
            ('cauteloso', CautiousStrategy),
            ('aleatorio', RandomStrategy),
        ])

        round_count = 0
        while round_count < MAX_ROUNDS:
            active = [p for p in ordered_players if p.active]
            if len(active) <= 1:
                break

            for player in ordered_players:
                if not player.active:
                    continue
                if len([p for p in ordered_players if p.active]) <= 1:
                    break

                player, properties = turn_resolver.resolve(
                    player, properties, ordered_players, round_count + 1,
                )
                self._update_player(player, ordered_players)
                properties = release_bankrupt_properties(ordered_players, properties, self._emit)

            round_count += 1

        winner, ranking = determine_winner(ordered_players)
        end_reason = 'um_jogador_restante' if len([p for p in ordered_players if p.active]) <= 1 else 'max_rodadas'

        self._emit(GameFinished(winner, round_count, end_reason))

        return SimulationResult(
            winner=winner,
            players=ranking,
            total_rounds=round_count,
            end_reason=end_reason,
        )

    def _create_players(self) -> List[Player]:
        from game.services.turn_resolver import PLAYER_TYPES
        return [
            Player(name=name, balance=INITIAL_BALANCE, position=0, active=True, turn_order=i)
            for i, (name, _) in enumerate(PLAYER_TYPES)
        ]

    def _update_player(self, player: Player, players: List[Player]) -> None:
        idx = next(i for i, p in enumerate(players) if p.name == player.name)
        players[idx] = player
