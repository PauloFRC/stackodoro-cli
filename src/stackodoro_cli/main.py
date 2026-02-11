from .presenter import display_view
from .state_manager import StateManager

import sys
import time
import click

@click.command()
def run():
    state_manager = StateManager()
    state_manager.start_pomodoro(work_minutes=1, break_minutes=1, big_break_minutes=10, n_cycles=2)

    sys.stdout.write("\033[2J") # clear screen

    try:
        sys.stdout.write("\033[?25l") # hide cursor
        
        while True:
            current_time = time.time()
            
            # if kb.check_space():
            #     is_paused = not is_paused
            #     if not is_paused:
            #         target_time = current_time + time_remaining


            sys.stdout.write("\033[2J") 
            
            state_manager.tick()

            display_view(state_manager)

            sys.stdout.write("\033[J")
            
            time.sleep(0.1) 
            
    except KeyboardInterrupt:
        sys.stdout.write("\033[?25h") # show cursor
        sys.stdout.write("\033[2J\033[H") # clear and home
        print("\nExiting Stackodoro...")
        sys.exit(0)

if __name__ == "__main__":
    run()
    