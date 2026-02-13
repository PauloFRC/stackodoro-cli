from .book import Book, book_options

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
    
    def _init_storage_path(self):
        data_home = os.getenv('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
        self.storage_dir = Path(data_home) / 'stackodoro-cli'
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.storage_file = self.storage_dir / 'bookshelf.json'
    
    def load(self):
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
    
    def render(self) -> tuple[list[str], list[list[str]]]:
        result_text: list[str] = []
        result_attrs: list[list[str]] = []
        
        def add_shelf_part(part_lines):
            result_text.extend(part_lines)
            for line in part_lines:
                result_attrs.append(['shelf_color'] * len(line))

        add_shelf_part(self.top)
        
        books_to_place: list[Book] = self._completed_books.copy()

        for shelf_i in range(self.n_shelfs):
            current_rows = ["||"] * SHELF_HEIGHT
            current_attrs = [['shelf_color'] * 2 for _ in range(SHELF_HEIGHT)]
            
            used_width = 0
            previous_book: Book | None = None  # track previous book for height comparison

            while books_to_place:
                next_book = books_to_place[0]
                is_first_book = (used_width == 0)
                effective_width = next_book.width if is_first_book else (next_book.width - 1)

                if used_width + effective_width <= self.shelf_width:
                    book = books_to_place.pop(0)
                    book_color = book.color

                    if is_first_book:
                        for i in range(SHELF_HEIGHT):
                            line_len = len(book.ascii[i])
                            current_rows[i] += book.ascii[i]
                            current_attrs[i].extend([book_color] * line_len)
                    else:
                        prev_h = sum(1 for line in previous_book.ascii if line.strip()) if previous_book else 0
                        curr_h = sum(1 for line in book.ascii if line.strip())
                        
                        collision_color = previous_book.color if previous_book and prev_h >= curr_h else book_color

                        for i in range(SHELF_HEIGHT):
                            left_char = current_rows[i][-1]
                            right_char = book.ascii[i][0]
                            merged_char = self._resolve_border(left_char, right_char)
                            
                            current_rows[i] = (
                                current_rows[i][:-1] + 
                                merged_char + 
                                book.ascii[i][1:]
                            )
                            
                            left_is_content = left_char != ' '
                            right_is_content = right_char != ' '
                            
                            if left_is_content and right_is_content:
                                final_border_color = collision_color
                            elif left_is_content:
                                final_border_color = previous_book.color if previous_book else 'shelf_color'
                            elif right_is_content:
                                final_border_color = book_color
                            else:
                                final_border_color = collision_color

                            current_attrs[i].pop()
                            current_attrs[i].append(final_border_color)
                            current_attrs[i].extend([book_color] * (len(book.ascii[i]) - 1))

                    used_width += effective_width
                    previous_book = book
                else:
                    break
            
            remaining_space = self.shelf_width - used_width
            if remaining_space > 0:
                for i in range(SHELF_HEIGHT):
                    current_rows[i] += " " * remaining_space
                    current_attrs[i].extend(['shelf_color'] * remaining_space)

            for i in range(SHELF_HEIGHT):
                current_rows[i] += "||"
                current_attrs[i].extend(['shelf_color'] * 2)
            
            result_text.extend(current_rows)
            result_attrs.extend(current_attrs)

            if shelf_i < self.n_shelfs - 1:
                add_shelf_part(self.mid)
        
        add_shelf_part(self.bottom)
        return result_text, result_attrs

    def __str__(self) -> str:
        text, _ = self.render()
        return "\n".join(text)
    