from .bookshelf import Bookshelf
from importlib import resources

from random import choice

def merge_lines(bg_line: str, fg_line: str) -> str:
    # identify solid bounds
    stripped_fg = fg_line.strip()
    if not stripped_fg:
        return bg_line

    first_char = stripped_fg[0]
    last_char = stripped_fg[-1]
    start_index = fg_line.find(first_char)
    end_index = fg_line.rfind(last_char)

    max_len = max(len(bg_line), len(fg_line))
    result = []

    for i in range(max_len):
        bg_char = bg_line[i] if i < len(bg_line) else ' '
        fg_char = fg_line[i] if i < len(fg_line) else ' '
        if i < start_index or i > end_index:
            result.append(bg_char)
        else:
            result.append(fg_char)

    return "".join(result).rstrip()

def display_view(usr_bookshelf):
    bs_lines = usr_bookshelf.ascii_list()

    with resources.files('stackodoro_cli').joinpath('res/table.txt').open('r') as f:
        table_lines = [line.rstrip('\n') for line in f]

    OVERLAP = 5
        
    env_view = bs_lines[:-OVERLAP]
    bs_overlap = bs_lines[-OVERLAP:]
    tbl_overlap = table_lines[:OVERLAP]

    for bg, fg in zip(bs_overlap, tbl_overlap):
        env_view.append(merge_lines(bg, fg))

    env_view.extend(table_lines[OVERLAP:])

    steam_variations = [
        [
            " " * 22 + "    ( )  ", 
            " " * 22 + "    ) (   "
            ],
            [
            " " * 22 + "   ( (   ", 
            " " * 22 + "    ) )  "
            ],
            [
            " " * 22 + "    ) (   ",
            " " * 22 + "    ( )   "
            ],
            [
            " " * 22 + "   ) )   ", 
            " " * 22 + "    ( (  "
            ],
            [
            " " * 22 + "    ( (  ", 
            " " * 22 + "   ) )   "
            ]
    ]
    steam_lines = choice(steam_variations)
    
    table_start_index = len(bs_lines) - OVERLAP
    steam_start_y = table_start_index - 1

    for i, steam_row in enumerate(steam_lines):
        target_y = steam_start_y + i
        
        if target_y < len(env_view):
            env_view[target_y] = merge_lines(env_view[target_y], steam_row)

    print("\n".join(env_view))
