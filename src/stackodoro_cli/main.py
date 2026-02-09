from .bookshelf import Bookshelf
from .presenter import display_view

import sys
import click
import time

@click.command()
def run():
    my_shelf = Bookshelf()
    for _ in range(5):
        my_shelf.add_book()

    try:
        sys.stdout.write("\033[?25l")
        while True:
            sys.stdout.write("\033[H\033[J")            
            display_view(my_shelf)
            time.sleep(0.6)
            
    except KeyboardInterrupt:
        sys.stdout.write("\033[?25h")
        print("\n\nExiting Stackodoro...")
        sys.exit(0)

if __name__ == "__main__":
    run()