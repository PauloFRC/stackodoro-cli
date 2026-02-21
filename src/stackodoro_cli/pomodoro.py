import time
from dataclasses import dataclass

from .messages import get_pomodoro_session_message
from .enums import SessionType

@dataclass
class PomodoroStatus:
    session_type: SessionType = SessionType.WORK
    time_remaining: int = 0
    is_paused: bool = False
    is_running: bool = False
    is_transition_pending: bool = False
    message: str = ""

class Pomodoro:
    def __init__(self, work_period:int = 25, break_period:int = 5, big_break_period:int = 30, n_cycles:int = 3):
        self.work_period = work_period
        self.break_period = break_period
        self.big_break_period = big_break_period
        self.n_cycles = n_cycles

        self._session_type: SessionType = SessionType.WORK
        self._time_remaining: int = self.work_period * 60
        self._cycles_completed: int = 0
        
        self._running = False
        self._paused = False
        self._transition_pending = False
        self._last_decrement: float | None = None
        self._message = ""
        self._update_message()
    
    def get_status(self):
        self._update_clock()
        return PomodoroStatus(
            self._session_type,
            int(self._time_remaining),
            self._paused,
            self._running,
            self._transition_pending,
            self._message
        )
    
    def _update_message(self):
        self._message = get_pomodoro_session_message(self._session_type)
    
    def _update_clock(self):
        if not self._running or self._paused or self._transition_pending:
            return

        now = time.time()
        if self._last_decrement is not None:
            elapsed = now - self._last_decrement
            self._time_remaining -= elapsed

        self._last_decrement = now

        if self._time_remaining <= 0:
            self._time_remaining = 0
            self._prepare_transition()
    
    def _prepare_transition(self):
        if self._session_type == SessionType.WORK:
            self._cycles_completed += 1
            # after n_cycles, use big break otherwise normal break
            if self._cycles_completed % self.n_cycles == 0:
                self._session_type = SessionType.BIG_BREAK
                self._time_remaining = self.big_break_period * 60
            else:
                self._session_type = SessionType.BREAK
                self._time_remaining = self.break_period * 60
        else: 
            self._session_type = SessionType.WORK
            self._time_remaining = self.work_period * 60
        
        self._update_message()
        
        self._transition_pending = True

    def confirm_transition(self, skip=False):
        if skip:
            self._prepare_transition()
        self._transition_pending = False
        self._last_decrement = time.time()
    
    def start(self):
        if not self._running:
            self._running = True
            self._paused = False
            self._last_decrement = time.time()
    
    def stop(self):
        self._running = False
    
    def pause(self):
        self._paused = True
    
    def play(self):
        self._paused = False
        self._last_decrement = time.time()
    
    def read(self) -> int:
        return self.time_remaining
        
    def transition(self):
        self._transition_pending = False
        self.play()
