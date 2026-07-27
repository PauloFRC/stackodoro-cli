import json
from itertools import dropwhile
import platformdirs
from pathlib import Path

from .models import AppSnapshot
from .book import Book

class StorageService:
    def __init__(self, storage_file: str | None=None):
        self.storage_file = storage_file        
        if not self.storage_file:
            self._load_default_storage()

        self.snapshot = self.load_state()

    def _load_default_storage(self):
        self.storage_dir = Path(platformdirs.user_data_dir("stackodoro-cli"))
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.storage_file = self.storage_dir / 'stackaro.json'

    def save_state(self, new_snapshot: AppSnapshot):
        data = {
            'playlist_dir': new_snapshot.playlist_dir,
            'n_shelfs_completed': new_snapshot.n_shelfs_completed,
            'books': [
                {
                    # drops starting empty lines so height is correctly calculated when reloadings
                    'ascii': list(dropwhile(lambda line: not line.strip(), book.ascii)),
                    'color': book.color
                }
                for book in new_snapshot.books
            ]
        }
        with open(self.storage_file, 'w') as f:
            json.dump(data, f, indent=2)

    def load_state(self) -> AppSnapshot:
        books = []
        n_completed = 0
        
        if self.storage_file.exists():
            try:
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    n_completed = data.get('n_shelfs_completed', 0)
                    for b in data.get('books', []):
                        books.append(Book(ascii=b['ascii'], color=b['color']))
                    
                    return AppSnapshot(
                        playlist_dir=data.get('playlist_dir') if 'data' in locals() else None,
                        n_shelfs_completed=n_completed,
                        books=books
                    )
                
            except (json.JSONDecodeError, KeyError):
                raise RuntimeError("Failed to load state: storage file is corrupted or has invalid format.")
        
        return AppSnapshot()
    
storage_service = StorageService()
