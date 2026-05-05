from importlib import resources
from random import choice

from dataclasses import dataclass, field

from .theme import BOOK_COLOR_NAMES

MAX_BOOK_HEIGHT = 8

@dataclass
class Book:
    ascii: list[str]
    color: str = 'default'
    height: int = field(init=False)
    width: int = field(init=False)
    
    def __post_init__(self):
        if len(self.ascii) > MAX_BOOK_HEIGHT:
            raise ValueError(f"Book has a height of {len(self.ascii)} lines, maximum allowed is {MAX_BOOK_HEIGHT}")

        self.height = len(self.ascii)
        self.width = max(len(line.rstrip("\n")) for line in self.ascii)

        if self.color == 'default':
            self.color = choice(BOOK_COLOR_NAMES)

        if len(self.ascii) < MAX_BOOK_HEIGHT:
            padding = [" " * self.width] * (MAX_BOOK_HEIGHT - len(self.ascii))
            lines = padding + self.ascii
            self.ascii = lines

def load_book_ascii(filename: str) -> list[str]:
    with resources.files('stackodoro_cli').joinpath(f'res/{filename}.txt').open('r') as f:
        return [line.rstrip('\n') for line in f]

book_options = [
    load_book_ascii(f"book{i}")
    for i in range(1, 21)
]
