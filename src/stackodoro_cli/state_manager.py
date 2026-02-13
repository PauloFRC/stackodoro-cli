from .bookshelf import Bookshelf
from .pomodoro import Pomodoro

class StateManager():
    def __init__(self):
        self.bookshelf = Bookshelf() # TODO: load from persistent storage
        self.is_paused = False
        self.pomodoro:Pomodoro | None = None
        self._timer_blink_visible = True

        self.steam_state = 0 
        self.max_steam_state = 4
        self.steam_tick_counter = 0
        self.steam_update_threshold = 12

    def tick(self):
        if self.pomodoro and self.pomodoro.time_remaining == 0:
            self._toggle_timer_blink_visibility()

        self.steam_tick_counter += 1
        if self.steam_tick_counter >= self.steam_update_threshold:
            self.steam_state = (self.steam_state + 1) % self.max_steam_state
            self.steam_tick_counter = 0
    
    def start_pomodoro(self, work_minutes=25, break_minutes=5, big_break_minutes=30, n_cycles=3):
        self.pomodoro = Pomodoro(work_minutes, break_minutes, big_break_minutes, n_cycles)
        self.pomodoro.start()
         
    def _toggle_timer_blink_visibility(self):
        self._timer_blink_visible = not self._timer_blink_visible
