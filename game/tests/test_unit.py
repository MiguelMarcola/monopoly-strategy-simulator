import unittest
from unittest.mock import MagicMock

from game.domain.board import BOARD_SIZE, DEFAULT_BOARD, create_default_board
from game.domain.constants import INITIAL_BALANCE, LAP_BONUS, MAX_ROUNDS
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
from game.services.turn_resolver import release_bankrupt_properties


class TestInitialGameSetup(unittest.TestCase):
    def test_four_players_created(self):
        simulator = GameSimulator()
        players = simulator._create_players()
        self.assertEqual(len(players), 4)

    def test_initial_balance_300_for_each(self):
        simulator = GameSimulator()
        players = simulator._create_players()
        for p in players:
            self.assertEqual(p.balance, INITIAL_BALANCE)

    def test_twenty_properties_on_board(self):
        properties = create_default_board()
        self.assertEqual(len(properties), 20)
        self.assertEqual(len(properties), BOARD_SIZE)

    def test_no_property_has_owner_initially(self):
        properties = create_default_board()
        for prop in properties:
            self.assertIsNone(prop.owner)
            self.assertTrue(prop.is_available())

    def test_turn_order_defined_for_players(self):
        simulator = GameSimulator()
        players = simulator._create_players()
        turn_orders = [p.turn_order for p in players]
        self.assertEqual(sorted(turn_orders), [0, 1, 2, 3])


class TestBoardMovement(unittest.TestCase):
    def test_move_without_completing_lap(self):
        from game.domain.board import move
        result = move(5, 3)
        self.assertEqual(result.new_position, 8)
        self.assertFalse(result.completed_lap)

    def test_move_completing_lap(self):
        from game.domain.board import move
        result = move(18, 4)
        self.assertEqual(result.new_position, 2)
        self.assertTrue(result.completed_lap)
        self.assertEqual(result.lap_bonus, LAP_BONUS)

    def test_position_wraps_with_modulo(self):
        self.assertEqual((19 + 1) % BOARD_SIZE, 0)
        self.assertEqual((0 + 6) % BOARD_SIZE, 6)


class TestLapBonus(unittest.TestCase):
    def test_lap_bonus_is_100(self):
        self.assertEqual(LAP_BONUS, 100)

    def test_player_gains_100_on_lap_completion(self):
        player = Player('test', 200, 0, True, 0)
        player = player.credit(LAP_BONUS)
        self.assertEqual(player.balance, 300)


class TestPropertyPurchase(unittest.TestCase):
    def test_purchase_decreases_balance(self):
        player = Player('impulsivo', 200, 0, True, 0)
        prop = Property(0, 100, 20)
        player = player.debit(prop.sale_cost)
        self.assertEqual(player.balance, 100)

    def test_property_receives_owner(self):
        prop = Property(0, 100, 20)
        new_prop = prop.with_owner('impulsivo')
        self.assertEqual(new_prop.owner, 'impulsivo')
        self.assertFalse(new_prop.is_available())


class TestPropertyRequiresRent(unittest.TestCase):
    def test_requires_rent_from_returns_false_for_own_property(self):
        prop = Property(0, 100, 20).with_owner('impulsivo')
        self.assertFalse(prop.requires_rent_from('impulsivo'))

    def test_requires_rent_from_returns_true_for_other_owner(self):
        prop = Property(0, 100, 20).with_owner('exigente')
        self.assertTrue(prop.requires_rent_from('impulsivo'))


class TestInsufficientBalance(unittest.TestCase):
    def test_cannot_afford_with_insufficient_balance(self):
        player = Player('impulsivo', 50, 0, True, 0)
        self.assertFalse(player.can_afford(100))

    def test_impulsive_does_not_buy_when_no_money(self):
        strategy = ImpulsiveStrategy()
        player = Player('impulsivo', 50, 0, True, 0)
        prop = Property(0, 100, 20)
        self.assertFalse(strategy.should_buy(player, prop))


class TestRentPayment(unittest.TestCase):
    def test_rent_debit_from_tenant(self):
        player = Player('exigente', 100, 0, True, 1)
        player = player.debit(50)
        self.assertEqual(player.balance, 50)

    def test_rent_credit_to_owner(self):
        owner = Player('impulsivo', 200, 0, True, 0)
        owner = owner.credit(50)
        self.assertEqual(owner.balance, 250)


class TestNoRentOnOwnProperty(unittest.TestCase):
    def test_property_requires_rent_from_excludes_owner(self):
        prop = Property(2, 120, 40).with_owner('impulsivo')
        self.assertFalse(prop.requires_rent_from('impulsivo'))


class TestBankruptcy(unittest.TestCase):
    def test_negative_balance_deactivates_player(self):
        player = Player('test', 50, 0, True, 0)
        player = player.debit(100)
        self.assertTrue(player.is_bankrupt())
        self.assertFalse(player.active)
        self.assertEqual(player.balance, -50)


class TestPropertyReleaseAfterBankruptcy(unittest.TestCase):
    def test_bankrupt_properties_become_available(self):
        players = [
            Player('a', -10, 0, False, 0),
            Player('b', 300, 0, True, 1),
        ]
        properties = [
            Property(0, 80, 20).with_owner('a'),
            Property(1, 100, 30),
        ]
        result = release_bankrupt_properties(players, properties, lambda e: None)
        self.assertIsNone(result[0].owner)
        self.assertTrue(result[0].is_available())

    def test_all_bankrupt_player_properties_released(self):
        players = [
            Player('falido', -50, 0, False, 0),
            Player('ativo', 300, 0, True, 1),
        ]
        properties = [
            Property(0, 80, 20).with_owner('falido'),
            Property(1, 100, 30).with_owner('falido'),
            Property(2, 120, 40),
        ]
        result = release_bankrupt_properties(players, properties, lambda e: None)
        self.assertIsNone(result[0].owner)
        self.assertIsNone(result[1].owner)
        self.assertTrue(result[0].is_available())
        self.assertTrue(result[1].is_available())
        self.assertIsNone(result[2].owner)

    def test_liberated_property_can_be_bought_again(self):
        prop = Property(0, 80, 20).with_owner('falido')
        prop = prop.without_owner()
        self.assertIsNone(prop.owner)
        self.assertTrue(prop.is_available())
        buyer = Player('comprador', 300, 0, True, 0)
        self.assertTrue(prop.can_be_bought_by(buyer))


class TestPlayerStrategies(unittest.TestCase):
    def test_impulsive_buys_any_property_with_balance(self):
        strategy = ImpulsiveStrategy()
        player = Player('impulsivo', 200, 0, True, 0)
        prop1 = Property(0, 100, 20)
        prop2 = Property(1, 100, 5)
        self.assertTrue(strategy.should_buy(player, prop1))
        self.assertTrue(strategy.should_buy(player, prop2))

    def test_impulsive_always_buys_when_can_afford(self):
        strategy = ImpulsiveStrategy()
        player = Player('impulsivo', 100, 0, True, 0)
        prop = Property(0, 100, 1)
        self.assertTrue(strategy.should_buy(player, prop))

    def test_demanding_buys_only_when_rent_gt_50(self):
        strategy = DemandingStrategy()
        player = Player('exigente', 200, 0, True, 1)
        self.assertTrue(strategy.should_buy(player, Property(0, 100, 51)))
        self.assertTrue(strategy.should_buy(player, Property(0, 100, 100)))
        self.assertFalse(strategy.should_buy(player, Property(0, 100, 50)))
        self.assertFalse(strategy.should_buy(player, Property(0, 100, 49)))

    def test_demanding_does_not_buy_rent_eq_50(self):
        strategy = DemandingStrategy()
        player = Player('exigente', 200, 0, True, 1)
        self.assertFalse(strategy.should_buy(player, Property(0, 100, 50)))

    def test_demanding_buys_rent_gt_50(self):
        strategy = DemandingStrategy()
        player = Player('exigente', 200, 0, True, 1)
        self.assertTrue(strategy.should_buy(player, Property(0, 100, 51)))

    def test_cautious_buys_only_with_80_reserve(self):
        strategy = CautiousStrategy()
        player = Player('cauteloso', 200, 0, True, 2)
        self.assertTrue(strategy.should_buy(player, Property(0, 100, 0)))
        self.assertTrue(strategy.should_buy(player, Property(0, 120, 0)))
        self.assertFalse(strategy.should_buy(player, Property(0, 121, 0)))

    def test_cautious_does_not_buy_if_reserve_79(self):
        strategy = CautiousStrategy()
        player = Player('cauteloso', 200, 0, True, 2)
        self.assertFalse(strategy.should_buy(player, Property(0, 121, 0)))

    def test_cautious_buys_if_reserve_80(self):
        strategy = CautiousStrategy()
        player = Player('cauteloso', 200, 0, True, 2)
        self.assertTrue(strategy.should_buy(player, Property(0, 120, 0)))

    def test_random_buys_when_random_returns_low(self):
        from unittest.mock import patch
        strategy = RandomStrategy()
        player = Player('aleatorio', 200, 0, True, 3)
        prop = Property(0, 100, 20)
        with patch('random.random', return_value=0.3):
            self.assertTrue(strategy.should_buy(player, prop))

    def test_random_does_not_buy_when_random_returns_high(self):
        from unittest.mock import patch
        strategy = RandomStrategy()
        player = Player('aleatorio', 200, 0, True, 3)
        prop = Property(0, 100, 20)
        with patch('random.random', return_value=0.7):
            self.assertFalse(strategy.should_buy(player, prop))


class TestZeroBalanceNotEliminated(unittest.TestCase):
    def test_zero_balance_player_stays_active(self):
        player = Player('test', 50, 0, True, 0)
        player = player.debit(50)
        self.assertEqual(player.balance, 0)
        self.assertTrue(player.active)
        self.assertFalse(player.is_bankrupt())


class TestDomainInvariants(unittest.TestCase):
    def test_player_position_always_between_0_and_19(self):
        from game.domain.board import move
        for start in range(BOARD_SIZE):
            for dice in range(1, 7):
                result = move(start, dice)
                self.assertGreaterEqual(result.new_position, 0)
                self.assertLess(result.new_position, BOARD_SIZE)

    def test_property_never_has_two_owners(self):
        prop = Property(0, 100, 20).with_owner('impulsivo')
        self.assertEqual(prop.owner, 'impulsivo')
        self.assertIsNone(prop.without_owner().owner)

    def test_failed_purchase_does_not_change_owner(self):
        prop = Property(0, 100, 20).with_owner('exigente')
        player = Player('impulsivo', 50, 0, True, 0)
        self.assertFalse(player.can_afford(prop.sale_cost))
        self.assertEqual(prop.owner, 'exigente')

    def test_rent_transfers_correctly_between_payer_and_owner(self):
        tenant = Player('impulsivo', 100, 0, True, 0)
        owner = Player('exigente', 200, 0, True, 1)
        rent = 30
        tenant_after = tenant.debit(rent)
        owner_after = owner.credit(rent)
        self.assertEqual(tenant_after.balance, 70)
        self.assertEqual(owner_after.balance, 230)
