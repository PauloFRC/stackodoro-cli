from .bookshelf import Bookshelf

import sys
import click

@click.command()
def run():
    usr_bookshelf = Bookshelf()
    for i in range(21):
        usr_bookshelf.add_book()
    print(str(usr_bookshelf))

if __name__ == "__main__":
    run()