from importlib import resources

from dataclasses import dataclass, field

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
    Book(load_book_ascii("book4"), color='book_color_4'),
    Book(load_book_ascii("book5"), color='book_color_5'),
    Book(load_book_ascii("book6"), color='book_color_6'),
    Book(load_book_ascii("book7"), color='book_color_7'),
    Book(load_book_ascii("book8"), color='book_color_8'),
    Book(load_book_ascii("book9"), color='book_color_9'),
    Book(load_book_ascii("book10"), color='book_color_10'),
    Book(load_book_ascii("book11"), color='book_color_1'),
    Book(load_book_ascii("book12"), color='book_color_2'),
    Book(load_book_ascii("book13"), color='book_color_3'),
    Book(load_book_ascii("book14"), color='book_color_4'),
    Book(load_book_ascii("book15"), color='book_color_5'),
    Book(load_book_ascii("book16"), color='book_color_6'),
    Book(load_book_ascii("book17"), color='book_color_7'),
    Book(load_book_ascii("book18"), color='book_color_8'),
    Book(load_book_ascii("book19"), color='book_color_9'),
    Book(load_book_ascii("book20"), color='book_color_10'),
]
