from .book import Book, book_options
from .models import AsciiArtAsset

from random import choice
import json
import os
from pathlib import Path

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
        self._init_storage_path()
        self._load()
    
    def _init_storage_path(self):
        data_home = os.getenv('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
        self.storage_dir = Path(data_home) / 'stackodoro-cli'
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.storage_file = self.storage_dir / 'bookshelf.json'
    
    def _load(self):
        if self.storage_file.exists():
            try:
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    self._completed_books = []
                    for book_data in data.get('books', []):
                        book = Book(
                            ascii=book_data['ascii'],
                            color=book_data['color']
                        )
                        self._completed_books.append(book)
            except (json.JSONDecodeError, KeyError):
                self._completed_books = []
    
    def save(self):
        data = {
            'books': [
                {
                    'ascii': book.ascii,
                    'color': book.color
                }
                for book in self._completed_books
            ]
        }
        with open(self.storage_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_book(self):
        self._completed_books.append(choice(book_options)) 

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
        
        books_to_place: list[Book] = self._completed_books.copy()

        for shelf_i in range(self.n_shelfs):
            current_rows = ["||"] * SHELF_HEIGHT
            current_attrs = [['shelf_color'] * 2 for _ in range(SHELF_HEIGHT)]
            
            used_width = 0
            previous_book: Book | None = None

            while books_to_place:
                next_book = books_to_place[0]
                is_first_book = (used_width == 0)
                effective_width = next_book.width if is_first_book else (next_book.width - 1)

                if used_width + effective_width <= self.shelf_width:
                    book = books_to_place.pop(0)
                    book_color = book.color

                    for i in range(SHELF_HEIGHT):
                        if is_first_book:
                            current_rows[i] += book.ascii[i]
                            current_attrs[i].extend([book_color] * len(book.ascii[i]))
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
                            current_attrs[i].extend([book_color] * (len(book.ascii[i]) - 1))

                    used_width += effective_width
                    previous_book = book
                else:
                    break
            
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
    