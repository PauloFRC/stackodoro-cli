from .models import AppState, AsciiArtAsset
from .utils import format_time, merge_assets, render_urwid_markup
from .pomodoro import SessionType

from importlib import resources
import random

def display_view(state: AppState) -> list:
    pomodoro_status = state.pomodoro_status
    if pomodoro_status and pomodoro_status.is_paused:
        return display_pause()

    base_canvas = AsciiArtAsset(
        lines=state.bookshelf_render.lines.copy(),
        colors=[row[:] for row in state.bookshelf_render.colors]
    )

    steam_variations = [
        [" " * 25 + "    ( (   ", " " * 25 + "     ) )  "],
        [" " * 25 + "   ) )    ", " " * 25 + "    ( (   "],
        [" " * 25 + "     ) )  ", " " * 25 + "    ( (   "],
        [" " * 25 + "    ( )   ", " " * 25 + "    ) (   "]
    ]
    steam_lines = steam_variations[state.steam_state]
    steam_asset = AsciiArtAsset(
        lines=steam_lines,
        colors=[['steam_color'] * len(line) for line in steam_lines]
    )

    with resources.files('stackodoro_cli').joinpath('res/table.txt').open('r') as f:
        table_lines = [line.rstrip('\n') for line in f]
    table_asset = AsciiArtAsset(
        lines=table_lines,
        colors=[['table_color'] * len(line) for line in table_lines]
    )

    OVERLAP = 6
    table_y = len(base_canvas) - OVERLAP
    steam_y = table_y - len(steam_asset)

    merge_assets(base_canvas, table_asset, table_y)
    merge_assets(base_canvas, steam_asset, steam_y)

    time_text = format_time(state.pomodoro_status.time_remaining) if state.pomodoro_status else '00:00'
    timer_str = " " * 42 + time_text
    timer_y = len(base_canvas) - 7
    timer_asset = AsciiArtAsset(
        lines=[timer_str],
        colors=[['timer_color'] * len(timer_str)]
    )
    
    merge_assets(base_canvas, timer_asset, timer_y)

    max_width = max(len(line) for line in base_canvas.lines) if base_canvas.lines else 0
    base_canvas.lines = [line.ljust(max_width) for line in base_canvas.lines]
    for row in base_canvas.colors:
        row.extend([None] * max(0, max_width - len(row)))

    if pomodoro_status and pomodoro_status.is_transition_pending:
        overlay_transition_modal(base_canvas, state)
    
    # add top sign when at least one shelf was completed
    if state.n_shelfs_completed > 0:
        final_canvas = completed_sign_asset(state.n_shelfs_completed)
        final_canvas.extend(base_canvas)
    else:
        final_canvas = base_canvas

    # add pomodoro session type info at the bottom
    if pomodoro_status:
        session_asset = AsciiArtAsset(
            lines=["", pomodoro_status.message],
            colors=["", ['session_color'] * len(pomodoro_status.message)]
        )
        final_canvas.extend(session_asset)

    # add music playing info at the bottom
    if state.music_playing:
        music_str = f"Playing {state.music_playing.split('/')[-1]}"
        music_playing_asset = AsciiArtAsset(
            lines=["", music_str],
            colors=["", ['music_color'] * len(music_str)]
        )
        final_canvas.extend(music_playing_asset)

    return render_urwid_markup(final_canvas)


def overlay_transition_modal(canvas: AsciiArtAsset, state: AppState) -> None:
    pomodoro_state = state.pomodoro_status
    if not pomodoro_state:
        return
    
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
        if y < len(canvas.lines):
            centered_modal = modal_line.center(len(canvas.lines[y]))
            canvas.lines[y] = centered_modal
            canvas.colors[y] = ['bold_text'] * len(centered_modal)


def display_pause() -> list:
    pause_msg = [
        "============",
        "   PAUSED   ",
        "============",
    ]
    return [('bold_text', "\n".join(pause_msg))]

def completed_sign_asset(n_completed:int) -> AsciiArtAsset:
    n_completed_txt = f"{min(n_completed, 99):02d}"

    with resources.files('stackodoro_cli').joinpath('res/sign.txt').open('r') as f:
        sign_lines = [line.rstrip('\n') for line in f]
    
    sign_lines[2] = sign_lines[2].replace("$$", n_completed_txt)
    return AsciiArtAsset(
        lines=sign_lines,
        colors=[['sign_color'] * len(line) for line in sign_lines]
    )

def session_type_info_asset(session_type: SessionType) -> AsciiArtAsset:


    return AsciiArtAsset(
        lines=[info_text],
        colors=[['session_color'] * len(info_text)]
    )