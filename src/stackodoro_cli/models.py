from enum import Enum
from dataclasses import dataclass, field

from .pomodoro import PomodoroStatus
from .book import Book

@dataclass
class AsciiArtAsset:
    lines: list[str] = field(default_factory=list)
    colors: list[list[str]] = field(default_factory=list)

    def extend(self, other: 'AsciiArtAsset'):
        self.lines.extend(other.lines)
        self.colors.extend(other.colors)

    def __len__(self) -> int:
        return len(self.lines)

@dataclass
class AsciiState:
    n_shelfs_completed: int = 0
    bookshelf_render: AsciiArtAsset | None = None
    pomodoro_status: PomodoroStatus | None = None
    steam_state: int = 0
    music_playing: str | None = None

@dataclass
class AppSnapshot:
    playlist_dir: str | None = None
    n_shelfs_completed: int = 0
    books: list[Book] = field(default_factory=list)
