from .models import AppState, AsciiArtAsset
from .utils import format_time, merge_layers_with_color, render_urwid_markup

from importlib import resources

def display_view(state: AppState):
    pomodoro_state = state.pomodoro_status
    if pomodoro_state and pomodoro_state.is_paused:
        return display_pause()

    # bookshelf_render is now an AsciiArtAsset object
    canvas_asset = state.bookshelf_render
    if not canvas_asset:
        return urwid.Text("") # Or your preferred empty state

    # 1. Prepare Steam Asset
    steam_variations = [
        [" " * 22 + "    ( (  ", " " * 22 + "     ) ) "],
        [" " * 22 + "   ) )   ", " " * 22 + "    ( (  "],
        [" " * 22 + "     ) )  ", " " * 22 + "    ( (   "],
        [" " * 22 + "    ( )   ", " " * 22 + "    ) (   "]
    ]
    steam_lines = steam_variations[state.steam_state]
    steam_asset = AsciiArtAsset(
        lines=steam_lines,
        colors=[['steam_color'] * len(line) for line in steam_lines]
    )

    # 2. Prepare Table Asset
    with resources.files('stackodoro_cli').joinpath('res/table.txt').open('r') as f:
        table_lines = [line.rstrip('\n') for line in f]
    table_asset = AsciiArtAsset(
        lines=table_lines,
        colors=[['table_color'] * len(line) for line in table_lines]
    )

    # 3. Layering Logic
    OVERLAP = 6
    # Use len(canvas_asset) thanks to our __len__ implementation
    table_y = len(canvas_asset) - OVERLAP
    steam_y = table_y - len(steam_asset) # Position steam relative to table height

    # Assuming merge_layers_with_color is updated to accept the Asset object
    # Or you can perform the merge on the underlying lines/colors
    canvas, attr_canvas = canvas_asset.lines.copy(), [row[:] for row in canvas_asset.colors]

    merge_layers_with_color(canvas, attr_canvas, table_asset.lines, table_y, 'table_color')
    merge_layers_with_color(canvas, attr_canvas, steam_asset.lines, steam_y, 'steam_color')

    # 4. Timer Logic
    time_text = format_time(state.pomodoro_status.time_remaining) if state.pomodoro_status else '00:00'
    timer_str = " " * 39 + time_text
    timer_y = len(canvas_asset) - 2
    
    merge_layers_with_color(canvas, attr_canvas, [timer_str], timer_y, 'timer_color')

    # 5. Final Formatting
    max_width = max(len(line) for line in canvas) if canvas else 0
    centered_canvas = [line.ljust(max_width) for line in canvas]

    if pomodoro_state and pomodoro_state.is_transition_pending:
        centered_canvas, attr_canvas = overlay_transition_modal(centered_canvas, attr_canvas, state)

    return render_urwid_markup(centered_canvas, attr_canvas)

def overlay_transition_modal(canvas: list[str], attr_canvas: list[list[str]], state: AppState) -> tuple[list[str], list[list[str]]]:
    pomodoro_state = state.pomodoro_status
    if not pomodoro_state:
        return canvas, attr_canvas
    
    block_type = pomodoro_state.session_type.value
    time_remaining = format_time(pomodoro_state.time_remaining)
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
    