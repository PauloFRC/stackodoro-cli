from .book import Book, book_options
from .models import AsciiArtAsset

from random import choice

SHELF_HEIGHT = 8

class Bookshelf: 
    def __init__(self, shelf_width=59, n_shelfs=2) -> None:
        self.shelf_width = shelf_width
        self.n_shelfs = n_shelfs

        self.top = [
           " " + ("_" * (self.shelf_width + 2)) + " " ,
           "||" + ("-" * self.shelf_width) + "||"
        ]
        self.mid = [
            "||" + ("-" * self.shelf_width) + "||"
        ] * 2
        self.bottom = [
            "||" + ("-" * self.shelf_width) + "||",
            "||" + ("_" * self.shelf_width) + "||"
        ]
        self._completed_books: list[Book] = []
        self.n_shelfs_completed: int = 0
    
    def _init_storage_path(self):
        data_home = os.getenv('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
        self.storage_dir = Path(data_home) / 'stackodoro-cli'
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.storage_file = self.storage_dir / 'bookshelf.json'
    
    def load_books(self, books: list[Book], n_shelfs_completed: int):
        self._completed_books = books
        self.n_shelfs_completed = n_shelfs_completed
    
    def get_books(self) -> list[Book]:
        return self._completed_books

    def get_n_shelfs_completed(self):
        return self.n_shelfs_completed
    
    def _pack_books(self, books: list[Book]) -> list[list[Book]]:
        shelves = []
        current_shelf = []
        used_width = 0

        for book in books:
            effective_width = book.width if not current_shelf else (book.width - 1)
            
            if used_width + effective_width <= self.shelf_width:
                current_shelf.append(book)
                used_width += effective_width
            else:
                # shelf full, start a new one
                shelves.append(current_shelf)
                current_shelf = [book]
                used_width = book.width

        if current_shelf:
            shelves.append(current_shelf)

        return shelves
    
    def add_book(self):
        new_book = choice(book_options)
        
        test_books = self._completed_books + [new_book]
        packed_shelves = self._pack_books(test_books)
        
        if len(packed_shelves) > self.n_shelfs:
            self.n_shelfs_completed += 1
            self._completed_books = [new_book]
        else:
            self._completed_books.append(new_book)

    def _resolve_border(self, left_char: str, right_char: str) -> str:
        # determines merged character priority
        if '|' in (left_char, right_char):
            return '|'
        if '.' in (left_char, right_char):
            return '.'
        if "'" in (left_char, right_char) or "`" in (left_char, right_char):
            return '^'
        return ' '

    def _add_shelf_part(self, part_lines) -> AsciiArtAsset:
            colors = [['shelf_color'] * len(line) for line in part_lines]
            return AsciiArtAsset(part_lines, colors)
    
    def render(self) -> AsciiArtAsset:
        result = AsciiArtAsset([], [])
        result.extend(self._add_shelf_part(self.top))
        
        packed_shelves = self._pack_books(self._completed_books)

        for shelf_i in range(self.n_shelfs):
            current_rows = ["||"] * SHELF_HEIGHT
            current_attrs = [['shelf_color'] * 2 for _ in range(SHELF_HEIGHT)]
            
            books_on_shelf = packed_shelves[shelf_i] if shelf_i < len(packed_shelves) else []
            used_width = 0
            previous_book: Book | None = None

            for index, book in enumerate(books_on_shelf):
                is_first_book = (index == 0)
                effective_width = book.width if is_first_book else (book.width - 1)
                used_width += effective_width

                for i in range(SHELF_HEIGHT):
                    if is_first_book:
                        current_rows[i] += book.ascii[i]
                        current_attrs[i].extend([book.color] * len(book.ascii[i]))
                    else:
                        left_char = current_rows[i][-1]
                        right_char = book.ascii[i][0]
                        merged_char = self._resolve_border(left_char, right_char)
                        
                        current_rows[i] = current_rows[i][:-1] + merged_char + book.ascii[i][1:]
                        
                        if book.height >= previous_book.height:
                            final_border_color = book.color
                        else:
                            final_border_color = previous_book.color

                        current_attrs[i].pop()
                        current_attrs[i].append(final_border_color)
                        current_attrs[i].extend([book.color] * (len(book.ascii[i]) - 1))

                previous_book = book
            
            remaining_space = self.shelf_width - used_width
            for i in range(SHELF_HEIGHT):
                line_padding = (" " * remaining_space) + "||"
                color_padding = ['shelf_color'] * (remaining_space + 2)
                current_rows[i] += line_padding
                current_attrs[i].extend(color_padding)

            result.extend(AsciiArtAsset(current_rows, current_attrs))

            if shelf_i < self.n_shelfs - 1:
                result.extend(self._add_shelf_part(self.mid))
        
        result.extend(self._add_shelf_part(self.bottom))
        return result

    def __str__(self) -> str:
        text, _ = self.render()
        return "\n".join(text)

    def __len__(self):
        return len(self._completed_books)
    