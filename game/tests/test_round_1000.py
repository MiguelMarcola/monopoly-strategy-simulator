import unittest

from game.domain.player import Player
from game.services.turn_resolver import determine_winner


class TestRound1000TieBreaker(unittest.TestCase):
    def test_tie_breaker_by_turn_order_when_equal_balance(self):
        players = [
            Player('impulsivo', 500, 0, True, 0),
            Player('exigente', 500, 0, True, 1),
            Player('cauteloso', 500, 0, True, 2),
            Player('aleatorio', 500, 0, True, 3),
        ]
        winner, ranking = determine_winner(players)
        self.assertEqual(winner, 'impulsivo')
        self.assertEqual(ranking, ['impulsivo', 'exigente', 'cauteloso', 'aleatorio'])

    def test_winner_is_highest_balance_then_turn_order(self):
        players = [
            Player('impulsivo', 100, 0, True, 0),
            Player('exigente', 200, 0, True, 1),
            Player('cauteloso', 200, 0, True, 2),
            Player('aleatorio', 150, 0, True, 3),
        ]
        winner, ranking = determine_winner(players)
        self.assertEqual(winner, 'exigente')
        self.assertEqual(ranking[0], 'exigente')
        self.assertEqual(ranking[1], 'cauteloso')
