from enum import Enum
import threading
import time
from dataclasses import dataclass

class SessionType(Enum):
    WORK = "work"
    BREAK = "break"
    BIG_BREAK = "big_break"

@dataclass
class PomodoroStatus:
    session_type: SessionType = SessionType.WORK
    time_remaining: int = 0
    is_paused: bool = False
    is_running: bool = False
    is_transition_pending: bool = False

class Pomodoro:
    def __init__(self, work_period:int = 25, break_period:int = 5, big_break_period:int = 30, n_cycles:int = 3):
        self.work_period = work_period
        self.break_period = break_period
        self.big_break_period = big_break_period
        self.n_cycles = n_cycles

        self._state: SessionType = SessionType.WORK
        self._time_remaining: int = self.work_period * 60
        self._cycles_completed: int = 0
        
        self._lock = threading.Lock()
        self._running = False
        self._paused = False
        self._transition_pending = False
        self._thread = None
        self._last_decrement = None
    
    def get_status(self):
        with self._lock:
            return PomodoroStatus(
                self._state,
                self._time_remaining,
                self._paused,
                self._running,
                self._transition_pending
            )
    
    def confirm_transition(self):
        with self._lock:
            self._transition_pending = False
            self._last_decrement = time.time()
    
    def _counter_thread(self):
        with self._lock:
            self._last_decrement = time.time()
        
        while self._running:
            current_time = time.time()
            
            with self._lock:
                elapsed = current_time - self._last_decrement
                
                if (not self._paused and not self._transition_pending and 
                self._time_remaining > 0 and elapsed >= 1.0):

                    self._time_remaining -= 1
                    self._last_decrement = current_time

                    if self._time_remaining == 0:
                        self._prepare_transition()
            
            time.sleep(0.05)
    
    def _prepare_transition(self):
        if self._state == SessionType.WORK:
            self.cycles_completed += 1
            # after n_cycles, use big break otherwise normal break
            if self.cycles_completed % self.n_cycles == 0:
                self._state = SessionType.BIG_BREAK
                self._time_remaining = self.big_break_period * 60
            else:
                self._state = SessionType.BREAK
                self._time_remaining = self.break_period * 60
        else: 
            self._state = SessionType.WORK
            self._time_remaining = self.work_period * 60
        
        self._transition_pending = True
    
    def start(self):
        with self._lock:
            if not self._running:
                self._running = True
                self._thread = threading.Thread(target=self._counter_thread, daemon=True)
                self._thread.start()
    
    def stop(self):
        with self._lock:
            self._running = False
    
    def pause(self):
        with self._lock:
            self._paused = True
    
    def play(self):
        with self._lock:
            self._paused = False
            self._last_decrement = time.time()
    
    def read(self) -> int:
        with self._lock:
            return self.time_remaining
        
    def transition(self):
        with self._lock:
            self._transition_pending = False
