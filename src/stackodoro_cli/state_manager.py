from .bookshelf import Bookshelf
from .pomodoro import Pomodoro

class StateManager():
    def __init__(self):
        self.bookshelf = Bookshelf() # TODO: load from persistent storage
        for i in range(20):
            self.bookshelf.add_book()
        self.is_paused = False
        self.pomodoro:Pomodoro | None = None
        self._timer_blink_visible = True
        self._last_pomodoro_paused_state = False

        self.steam_state = 0 
        self.max_steam_state = 4
        self.steam_tick_counter = 0
        self.steam_update_threshold = 12

    def tick(self):
        if not self.pomodoro or (self.pomodoro and not self.is_transition_pending()):
            self.steam_tick_counter += 1
            if self.steam_tick_counter >= self.steam_update_threshold:
                self.steam_state = (self.steam_state + 1) % self.max_steam_state
                self.steam_tick_counter = 0
        
    def start_pomodoro(self, work_minutes=25, break_minutes=5, big_break_minutes=30, n_cycles=3):
        self.pomodoro = Pomodoro(work_minutes, break_minutes, big_break_minutes, n_cycles)
        self.pomodoro.start()
    
    def pause_pomodoro(self):
        if self.pomodoro:
            self.pomodoro.pause()
            self.is_paused = True
    
    def play_pomodoro(self):
        if self.pomodoro:
            self.pomodoro.play()
            self.is_paused = False
            self.transition_pending = False
    
    def is_transition_pending(self):
        return self.pomodoro._transition_pending if self.pomodoro else False
    
    def transition(self):
        if self.pomodoro:
            self.pomodoro.transition()
         
    def _toggle_timer_blink_visibility(self):
        self._timer_blink_visible = not self._timer_blink_visible
