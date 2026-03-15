import random
import unittest
from copy import deepcopy
from unittest.mock import MagicMock, patch

from game.domain.board import create_default_board
from game.domain.constants import MAX_ROUNDS
from game.domain.events import DiceRolled, PlayerBankrupted
from game.domain.player import Player
from game.domain.property import Property
from game.domain.strategies import (
    CautiousStrategy,
    DemandingStrategy,
    ImpulsiveStrategy,
    RandomStrategy,
)
from game.services.dice import Dice
from game.services.simulator import GameSimulator
from game.services.turn_resolver import TurnResolver, determine_winner


class TestSimulationFlow(unittest.TestCase):
    def test_game_ends_with_one_winner(self):
        simulator = GameSimulator()
        result = simulator.simulate()
        self.assertIn(result.winner, ['impulsivo', 'exigente', 'cauteloso', 'aleatorio'])
        self.assertEqual(result.players[0], result.winner)
        self.assertEqual(len(result.players), 4)

    def test_ranking_ordered_by_balance(self):
        random.seed(123)
        simulator = GameSimulator()
        result = simulator.simulate()
        self.assertEqual(result.players[0], result.winner)

    def test_winner_in_ranking_list(self):
        simulator = GameSimulator()
        result = simulator.simulate()
        self.assertIn(result.winner, result.players)

    def test_no_duplicate_players_in_ranking(self):
        simulator = GameSimulator()
        result = simulator.simulate()
        self.assertEqual(len(result.players), len(set(result.players)))

    def test_result_has_total_rounds_and_end_reason(self):
        simulator = GameSimulator()
        result = simulator.simulate()
        self.assertIsInstance(result.total_rounds, int)
        self.assertIn(result.end_reason, ['um_jogador_restante', 'max_rodadas'])


class TestMaxRounds(unittest.TestCase):
    def test_max_rounds_constant_is_1000(self):
        self.assertEqual(MAX_ROUNDS, 1000)


class TestTieBreaker(unittest.TestCase):
    def test_tie_breaker_by_turn_order(self):
        players = [
            Player('impulsivo', 100, 0, True, 0),
            Player('exigente', 100, 0, True, 1),
            Player('cauteloso', 100, 0, True, 2),
            Player('aleatorio', 100, 0, True, 3),
        ]
        winner, ranking = determine_winner(players)
        self.assertEqual(winner, 'impulsivo')
        self.assertEqual(ranking[0], 'impulsivo')


class TestLapBonusInSimulation(unittest.TestCase):
    def test_player_receives_bonus_on_lap(self):
        dice = MagicMock(spec=Dice)
        dice.roll.return_value = 5
        turn_resolver = TurnResolver(dice, lambda e: None, [
            ('impulsivo', ImpulsiveStrategy),
            ('exigente', DemandingStrategy),
            ('cauteloso', CautiousStrategy),
            ('aleatorio', RandomStrategy),
        ])
        player = Player('exigente', 300, 18, True, 1)
        properties = deepcopy(create_default_board())
        properties[3] = Property(3, 140, 50).with_owner(player.name)
        players = [Player('impulsivo', 300, 0, True, 0), player, Player('cauteloso', 300, 0, True, 2), Player('aleatorio', 300, 0, True, 3)]
        player, _ = turn_resolver.resolve(player, properties, players, 1)
        self.assertEqual(player.balance, 400)
        self.assertEqual(player.position, 3)


class TestLiberatedPropertyCanBeBought(unittest.TestCase):
    def test_another_player_can_buy_liberated_property(self):
        board = create_default_board()
        properties = [Property(0, 80, 20).without_owner()] + board[1:]
        player = Player('impulsivo', 300, 0, True, 0)
        self.assertTrue(properties[0].is_available())
        self.assertTrue(player.can_afford(80))

    def test_liberated_property_bought_in_future_turn(self):
        board = [Property(i, 100, 20) for i in range(20)]
        board[1] = Property(1, 100, 20).without_owner()
        players = [
            Player('falido', -10, 0, False, 0),
            Player('impulsivo', 300, 0, True, 0),
            Player('exigente', 300, 0, True, 1),
            Player('cauteloso', 300, 0, True, 2),
        ]
        dice = MagicMock(spec=Dice)
        dice.roll.return_value = 1
        turn_resolver = TurnResolver(dice, lambda e: None, [
            ('impulsivo', ImpulsiveStrategy),
            ('exigente', DemandingStrategy),
            ('cauteloso', CautiousStrategy),
            ('aleatorio', RandomStrategy),
        ])
        player, properties = turn_resolver.resolve(players[1], board, players, 1)
        self.assertEqual(properties[1].owner, 'impulsivo')
        self.assertFalse(properties[1].is_available())


class TestNoDuplicateOwners(unittest.TestCase):
    def test_property_has_single_owner(self):
        prop = Property(0, 100, 30).with_owner('impulsivo')
        self.assertEqual(prop.owner, 'impulsivo')
        self.assertIsNotNone(prop.owner)


class TestDeterministicSimulation(unittest.TestCase):
    def test_same_seed_produces_same_result(self):
        random.seed(999)
        sim1 = GameSimulator()
        result1 = sim1.simulate()
        random.seed(999)
        sim2 = GameSimulator()
        result2 = sim2.simulate()
        self.assertEqual(result1.winner, result2.winner)
        self.assertEqual(result1.players, result2.players)


class TestSimulatorWorksWithoutLogger(unittest.TestCase):
    def test_simulate_without_observer_returns_valid_result(self):
        simulator = GameSimulator(event_observer=None)
        result = simulator.simulate()
        self.assertIn(result.winner, ['impulsivo', 'exigente', 'cauteloso', 'aleatorio'])
        self.assertEqual(len(result.players), 4)


class TestBankruptPlayerNoMoreTurns(unittest.TestCase):
    def test_bankrupt_player_does_not_receive_turns_after_bankruptcy(self):
        bankrupt_rounds = {}
        dice_rolls_by_player = {}

        def collect(event):
            if isinstance(event, PlayerBankrupted):
                bankrupt_rounds[event.player_name] = event.round_num
            elif isinstance(event, DiceRolled):
                if event.player_name not in dice_rolls_by_player:
                    dice_rolls_by_player[event.player_name] = []
                dice_rolls_by_player[event.player_name].append(event.round_num)

        simulator = GameSimulator(event_observer=collect)
        result = simulator.simulate()

        for player_name, round_bankrupt in bankrupt_rounds.items():
            rolls_after = [r for r in dice_rolls_by_player.get(player_name, []) if r > round_bankrupt]
            self.assertEqual(rolls_after, [], f'{player_name} recebeu turnos apos falencia na rodada {round_bankrupt}')


class TestOnePlayerRemaining(unittest.TestCase):
    def test_when_one_player_remains_game_ends_with_correct_reason(self):
        board = [Property(i, 100, 20) for i in range(20)]
        board[1] = Property(1, 100, 310)
        dice = MagicMock(spec=Dice)
        dice.roll.return_value = 1
        simulator = GameSimulator(dice=dice, board=board, player_order=[0, 1, 2, 3])
        result = simulator.simulate()
        self.assertEqual(result.end_reason, 'um_jogador_restante')
        self.assertIn(result.winner, ['impulsivo', 'exigente', 'cauteloso', 'aleatorio'])
        self.assertEqual(len(result.players), 4)


class TestDeterministicWithMock(unittest.TestCase):
    def test_mock_dice_and_player_order_produces_same_result(self):
        dice = MagicMock(spec=Dice)
        dice.roll.return_value = 2
        with patch('random.random', return_value=0.3):
            sim1 = GameSimulator(dice=dice, player_order=[0, 1, 2, 3])
            result1 = sim1.simulate()
        dice.roll.return_value = 2
        with patch('random.random', return_value=0.3):
            sim2 = GameSimulator(dice=dice, player_order=[0, 1, 2, 3])
            result2 = sim2.simulate()
        self.assertEqual(result1.winner, result2.winner)
        self.assertEqual(result1.players, result2.players)
        self.assertEqual(result1.total_rounds, result2.total_rounds)
