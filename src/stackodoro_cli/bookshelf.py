from .book import Book, book_options

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

    def __str__(self) -> str:
        result: list[str] = self.top.copy()
        books_to_place: list[Book] = self._completed_books.copy()

        for shelf_i in range(self.n_shelfs):
            current_shelf_rows = ["||"] * SHELF_HEIGHT
            used_width = 0

            while books_to_place:
                next_book = books_to_place[0]
                is_first_book = (used_width == 0)
                effective_width = next_book.width if is_first_book else (next_book.width - 1)

                if used_width + effective_width <= self.shelf_width:
                    book = books_to_place.pop(0)

                    if is_first_book:
                        for i in range(SHELF_HEIGHT):
                            current_shelf_rows[i] += book.ascii[i]
                    else:
                        for i in range(SHELF_HEIGHT):
                            left_char = current_shelf_rows[i][-1]
                            right_char = book.ascii[i][0]
                            
                            merged_char = self._resolve_border(left_char, right_char)
                            
                            current_shelf_rows[i] = (
                                current_shelf_rows[i][:-1] + 
                                merged_char + 
                                book.ascii[i][1:]
                            )

                    used_width += effective_width
                else:
                    break
            
            # add rest of bookshelf padding
            remaining_space = self.shelf_width - used_width
            if remaining_space > 0:
                for i in range(SHELF_HEIGHT):
                    current_shelf_rows[i] += " " * remaining_space

            for i in range(SHELF_HEIGHT):
                current_shelf_rows[i] += "||"
            
            result.extend(current_shelf_rows)

            # add shelf separator if not last shelf
            if shelf_i < self.n_shelfs - 1:
                result.extend(self.mid)
        
        result.extend(self.bottom)
        return "\n".join(result)
        