from .state_manager import StateManager
from .bookshelf import Bookshelf
from .utils import merge_layers, center_canvas_on_screen, format_time

from importlib import resources

def display_view(state_manager: StateManager):
    
    if state_manager.is_paused:
        display_pause()
        return

    bs_lines = state_manager.bookshelf.ascii_list()

    with resources.files('stackodoro_cli').joinpath('res/table.txt').open('r') as f:
        table_lines = [line.rstrip('\n') for line in f]

    steam_variations = [
        [
            " " * 22 + "    ( (  ", 
            " " * 22 + "     ) ) "
            ],
            [
            " " * 22 + "   ) )   ", 
            " " * 22 + "    ( (  "
            ],
            [
            " " * 22 + "     ) )  ", 
            " " * 22 + "    ( (   "
            ],
            [
            " " * 22 + "    ( )   ", 
            " " * 22 + "    ) (   "
            ]
    ]
    steam_lines = steam_variations[state_manager.steam_state]

    canvas = bs_lines
    
    OVERLAP = 6
    table_y = len(canvas) - OVERLAP
    steam_y = table_y - 1

    canvas = merge_layers(canvas, table_lines, table_y)
    canvas = merge_layers(canvas, steam_lines, steam_y)

    timer_str = " " * 39 + f"{format_time(state_manager.pomodoro.read()) if state_manager.pomodoro else '00:00'}"
    
    timer_y = len(bs_lines) - 2
    
    canvas = merge_layers(canvas, [timer_str], timer_y)

    max_width = max(len(line) for line in canvas) if canvas else 0
    centered_canvas = [line.ljust(max_width) for line in canvas]

    print("\n".join(centered_canvas))

def display_pause():
    pause_msg = [
            "============",
            "   PAUSED   ",
            "============",
        ]
    print("\n".join(pause_msg))
    