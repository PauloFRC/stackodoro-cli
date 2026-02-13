from .state_manager import StateManager
from .utils import format_time, merge_layers_with_color, render_urwid_markup

from importlib import resources

def display_view(state_manager: StateManager):
    
    if state_manager.is_paused:
        return display_pause()

    bs_lines, bs_attrs = state_manager.bookshelf.render()

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

    canvas = bs_lines.copy()
    attr_canvas: list[list[str|None]] = [row[:] for row in bs_attrs]

    merge_layers_with_color(canvas, attr_canvas, [], 0, None)
    
    OVERLAP = 6
    table_y = len(canvas) - OVERLAP
    steam_y = table_y - 1

    merge_layers_with_color(canvas, attr_canvas, table_lines, table_y, 'table_color')

    merge_layers_with_color(canvas, attr_canvas, steam_lines, steam_y, 'steam_color')

    timer_str = " " * 39 + f"{format_time(state_manager.pomodoro.read()) if state_manager.pomodoro else '00:00'}"
    
    timer_y = len(bs_lines) - 2
    
    merge_layers_with_color(canvas, attr_canvas, [timer_str], timer_y, 'timer_color')

    max_width = max(len(line) for line in canvas) if canvas else 0
    centered_canvas = [line.ljust(max_width) for line in canvas]

    if state_manager.is_transition_pending():
        centered_canvas, attr_canvas = overlay_transition_modal(centered_canvas, attr_canvas, state_manager)

    return render_urwid_markup(centered_canvas, attr_canvas)

def overlay_transition_modal(canvas: list[str], attr_canvas: list[list[str]], state_manager: StateManager) -> tuple[list[str], list[list[str]]]:
    if not state_manager.pomodoro:
        return canvas, attr_canvas
    
    block_type = state_manager.pomodoro.state.value
    time_remaining = format_time(state_manager.pomodoro.read())
    type_display = {
        'work': 'Work',
        'break': 'Break',
        'big_break': 'Big Break'
    }
    
    block_name = type_display.get(block_type, 'Unknown')
    
    WIDTH = 80
    modal_lines = [
        "=" * WIDTH,
        " " * WIDTH,
        f"Press space to start {block_name} timer".center(WIDTH),
        str(time_remaining).center(WIDTH),
        " " * WIDTH,
        "=" * WIDTH,
    ]

    canvas_height = len(canvas)
    modal_height = len(modal_lines)
    
    start_y = max(0, (canvas_height - modal_height) // 2)    
    for i, modal_line in enumerate(modal_lines):
        y = start_y + i
        if y < len(canvas):
            centered_modal = modal_line.center(len(canvas[y]))
            canvas[y] = centered_modal
            attr_canvas[y] = ['bold_text'] * len(centered_modal)
    
    return canvas, attr_canvas

def display_pause():
    pause_msg = [
            "============",
            "   PAUSED   ",
            "============",
        ]
    return [('bold_text', "\n".join(pause_msg))]
    