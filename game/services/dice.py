import random


class Dice:
    FACES = 6

    def roll(self) -> int:
        return random.randint(1, self.FACES)
