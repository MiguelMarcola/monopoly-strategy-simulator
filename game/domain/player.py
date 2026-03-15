from dataclasses import dataclass


@dataclass
class Player:
    name: str
    balance: int
    position: int
    active: bool
    turn_order: int

    def can_afford(self, amount: int) -> bool:
        return self.balance >= amount and self.active

    def is_bankrupt(self) -> bool:
        return self.balance < 0

    def debit(self, amount: int) -> 'Player':
        new_balance = self.balance - amount
        return Player(
            name=self.name,
            balance=new_balance,
            position=self.position,
            active=new_balance >= 0,
            turn_order=self.turn_order,
        )

    def credit(self, amount: int) -> 'Player':
        return Player(
            name=self.name,
            balance=self.balance + amount,
            position=self.position,
            active=self.active,
            turn_order=self.turn_order,
        )

    def move_to(self, position: int) -> 'Player':
        return Player(
            name=self.name,
            balance=self.balance,
            position=position,
            active=self.active,
            turn_order=self.turn_order,
        )
