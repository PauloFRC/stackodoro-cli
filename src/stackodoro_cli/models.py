from enum import Enum, auto
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
class MenuState:
    show_menus: bool = True
    show_volume: bool = False
    volume: float = 1.0
    show_custom_timer_dialog: bool = False
    show_playlist_picker_dialog: bool = False
    current_playlist_dir: str = ""
    error_msg: str | None = None
    
@dataclass
class UIState:
    ascii: AsciiState = field(default_factory=AsciiState)
    menu: MenuState = field(default_factory=MenuState)

# actions
class UIElement(Enum):
    MENUS = auto()
    VOLUME = auto()
    CUSTOM_TIMER_DIALOG = auto()
    PLAYLIST_PICKER_DIALOG = auto()
    ERROR_MSG = auto()

@dataclass(frozen=True)
class SetVisible:
    element: UIElement
    visible: bool

@dataclass(frozen=True)
class Tick: pass

@dataclass(frozen=True)
class AdjustVolume:
    delta: float

@dataclass(frozen=True)
class PlaySessionCompletedSound: pass

@dataclass(frozen=True)
class PlayShelfCompletedSound: pass

@dataclass(frozen=True)
class PlayPlaylist: pass

@dataclass(frozen=True)
class StopPlaylist: pass

@dataclass(frozen=True)
class PausePlaylist: pass

@dataclass(frozen=True)
class ToggleMusic: pass

@dataclass(frozen=True)
class PreviousTrack: pass

@dataclass(frozen=True)
class NextTrack: pass

@dataclass(frozen=True)
class TogglePause: pass

@dataclass(frozen=True)
class StartTimer:
    work_minutes: int
    break_minutes: int
    big_break_minutes: int

@dataclass(frozen=True)
class SetPlaylistDir:
    directory: str

@dataclass(frozen=True)
class DisplayError:
    error_msg: str

@dataclass(frozen=True)
class Quit: pass

Action = Tick | DisplayError | SetVisible | AdjustVolume | ToggleMusic | PreviousTrack | NextTrack | TogglePause | StartTimer | PlayPlaylist | StopPlaylist | PausePlaylist | SetPlaylistDir | Quit | PlaySessionCompletedSound | PlayShelfCompletedSound

@dataclass
class AppSnapshot:
    playlist_dir: str | None = None
    n_shelfs_completed: int = 0
    books: list[Book] = field(default_factory=list)
