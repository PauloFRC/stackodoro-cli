from .pomodoro import PomodoroStatus

from dataclasses import dataclass, field

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
class AppState:
    n_shelfs_completed: int = 0
    bookshelf_render: AsciiArtAsset | None = None
    pomodoro_status: PomodoroStatus | None = None
    steam_state: int = 0
