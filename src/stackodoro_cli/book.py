from importlib import resources

from dataclasses import dataclass, field

MAX_BOOK_HEIGHT = 8

@dataclass
class Book:
    ascii: list[str]
    color: str = 'default'
    height: int = field(init=False)

    @property
    def width(self) -> int:
        return max(len(line.rstrip("\n")) for line in self.ascii)
    
    def __post_init__(self):
        if len(self.ascii) > MAX_BOOK_HEIGHT:
            raise ValueError(f"Book has a height of {len(self.ascii)} lines, maximum allowed is {MAX_BOOK_HEIGHT}")

        self.height = len(self.ascii)

        if len(self.ascii) < MAX_BOOK_HEIGHT:
            padding = [" " * self.width] * (MAX_BOOK_HEIGHT - len(self.ascii))
            lines = padding + self.ascii
            self.ascii = lines

def load_book_ascii(filename: str) -> list[str]:
    with resources.files('stackodoro_cli').joinpath(f'res/{filename}.txt').open('r') as f:
        return [line.rstrip('\n') for line in f]

book_options = [
    Book(load_book_ascii("book1"), color='book_color_1'),
    Book(load_book_ascii("book2"), color='book_color_2'),
    Book(load_book_ascii("book3"), color='book_color_3'),
]
