from .bookshelf import Bookshelf
from .utils import merge_layers
from importlib import resources

from random import choice

def display_view(usr_bookshelf: Bookshelf):
    bs_lines = usr_bookshelf.ascii_list()

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
    steam_lines = choice(steam_variations)

    canvas = bs_lines
    
    OVERLAP = 6
    table_y = len(canvas) - OVERLAP
    steam_y = table_y - 1

    canvas = merge_layers(canvas, table_lines, table_y)
    canvas = merge_layers(canvas, steam_lines, steam_y)

    print("\n".join(canvas))