import urwid
import json
import os
from pathlib import Path

from .menus import LeftMenu, RightMenu, CustomTimerDialog
from .theme import palette
from .models import AppState
from .pomodoro import Pomodoro, SessionType
from .bookshelf import Bookshelf
from .book import Book
from .presenter import display_view
from .audio import AudioMixer

class App:
    def __init__(self):
        self.state = AppState()

        # services
        self.bookshelf = Bookshelf()
        self._init_storage()
        self._load_data()
        self.pomodoro = None
        self.mixer = AudioMixer()
        
        # ASCII art display
        self.display_text = urwid.Text("", align='center', wrap='clip')
        self.display_box = urwid.Filler(self.display_text, 'middle')
        
        # menus
        self.left_menu = LeftMenu(
            on_preset=self.start_preset, 
            on_custom=self.show_custom_dialog, 
            on_quit=self.quit_app
        )
        self.right_menu = RightMenu(
            on_music=self.toggle_music
        )
        
        self.empty_side = urwid.Filler(urwid.Text(""), 'middle')
        self.columns = urwid.Columns([
            ('weight', 1, self.left_menu),
            ('weight', 3, self.display_box),
            ('weight', 1, self.right_menu),
        ])
        
        self.main_widget = self.columns
        self.loop = urwid.MainLoop(
            self.main_widget,
            palette=palette,
            unhandled_input=self.handle_input
        )

        self._hide_alarm = None
        self.steam_tick_counter = 0
        self.steam_update_threshold = 12
        self.menus_visible = True
        self.active_dialog: CustomTimerDialog | None = None
        self._transition_sound_played = False

        # for now, plays session complete effect on init
        self.mixer.play_session_complete()
        
        self.loop.set_alarm_in(0.1, self.update_display)
    
    def _init_storage(self):
        data_home = os.getenv('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
        self.storage_dir = Path(data_home) / 'stackodoro-cli'
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.storage_file = self.storage_dir / 'bookshelf.json'
        
    def _load_data(self):
        books = []
        n_completed = 0
        
        if self.storage_file.exists():
            try:
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    n_completed = data.get('n_shelfs_completed', 0)
                    for b in data.get('books', []):
                        books.append(Book(ascii=b['ascii'], color=b['color']))
            except (json.JSONDecodeError, KeyError):
                pass
                
        self.bookshelf.load_books(books, n_completed)
        self.state.n_shelfs_completed = n_completed
        
    def save_data(self):
        data = {
            'n_shelfs_completed': self.bookshelf.n_shelfs_completed,
            'books': [
                {
                    'ascii': book.ascii,
                    'color': book.color
                }
                for book in self.bookshelf.get_books()
            ]
        }
        with open(self.storage_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _auto_hide_menus(self, loop, user_data):
        self.hide_menus()
        self._hide_alarm = None
    
    # autohide menu after 5 seconds
    def _schedule_autohide(self):
        if self._hide_alarm:
            self.loop.remove_alarm(self._hide_alarm)
        self._hide_alarm = self.loop.set_alarm_in(5, self._auto_hide_menus)
    
    def hide_menus(self):
        self.menus_visible = False
        self.columns.contents[0] = (self.empty_side, self.columns.options('weight', 1))
        self.columns.contents[2] = (self.empty_side, self.columns.options('weight', 1))
    
    def show_menus(self):
        self.menus_visible = True
        self.columns.contents[0] = (self.left_menu, self.columns.options('weight', 1))
        self.columns.contents[2] = (self.right_menu, self.columns.options('weight', 1))
    
    # start session
    def start_preset(self, work_minutes, break_minutes, big_break_minutes):
        if self.pomodoro:
            self.pomodoro.stop()
            
        self.pomodoro = Pomodoro(
            work_period=work_minutes,
            break_period=break_minutes,
            big_break_period=big_break_minutes,
            n_cycles=3
        )
        self.pomodoro.start()
        self.hide_menus()
    
    # custom pomodoro dialog
    def show_custom_dialog(self):
        if self.active_dialog:
            return
            
        self.active_dialog = CustomTimerDialog(
            on_start=self.start_custom_timer,
            on_cancel=self.close_custom_dialog
        )
        
        overlay = urwid.Overlay(
            self.active_dialog,
            self.main_widget,
            align='center',
            width=('relative', 40),
            valign='middle',
            height=('relative', 40)
        )
        
        self.loop.widget = overlay
    
    def start_custom_timer(self, work, break_time, big_break):
        self.close_custom_dialog()
        self.start_preset(work, break_time, big_break)
    
    def close_custom_dialog(self):
        self.active_dialog = None
        self.loop.widget = self.main_widget
    
    def toggle_pause(self):
        if not self.pomodoro:
            return
            
        pomodoro_state = self.pomodoro.get_status()
        
        if pomodoro_state.is_transition_pending:
            self.handle_transition()
        elif pomodoro_state.is_paused:
            self.pomodoro.play()
        else:
            self.pomodoro.pause()

    def handle_transition(self):
        pomodoro_state = self.pomodoro.get_status()
        
        # if we are no longer in WORK (meaning work finished), add a book
        if pomodoro_state.session_type != SessionType.WORK:
            self.bookshelf.add_book()
            self.save_data()
            
        self.pomodoro.confirm_transition()
    
    def toggle_music(self):
        pass
    
    def quit_app(self):
        self.save_data()
        if self.pomodoro:
            self.pomodoro.stop()
        if self.mixer:
            self.mixer.quit()
        raise urwid.ExitMainLoop()
    
    def handle_input(self, key):
        if self.active_dialog:
            if key == 'esc':
                self.close_custom_dialog()
            elif key == 'enter':
                self.active_dialog.try_submit()
            return
        
        if key in ('q', 'Q'):
            self.quit_app()
        elif key == ' ':
            if self.pomodoro:
                self.toggle_pause()
        else:
            if not self.menus_visible:
                self.show_menus()
                if self.pomodoro:
                    self._schedule_autohide()
            return key

    def update_animations(self):
        pomodoro_state = self.state.pomodoro_status

        # update steam
        if not pomodoro_state or (not pomodoro_state.is_paused and not pomodoro_state.is_transition_pending):
            self.steam_tick_counter += 1
            if self.steam_tick_counter >= self.steam_update_threshold:
                self.state.steam_state = (self.state.steam_state + 1) % 4
                self.steam_tick_counter = 0
    
    def update_display(self, loop, user_data=None):
        self.state.bookshelf_render = self.bookshelf.render()
        self.state.n_shelfs_completed = self.bookshelf.get_n_shelfs_completed()

        if self.pomodoro:
            self.state.pomodoro_status = self.pomodoro.get_status()
            
            # play session complete sound effect
            if self.state.pomodoro_status.is_transition_pending:
                if not self._transition_sound_played:
                    self.mixer.play_session_complete()
                    self._transition_sound_played = True
            else:
                self._transition_sound_played = False

        self.update_animations()

        markup_content = display_view(self.state)
        self.display_text.set_text(markup_content)
        
        loop.set_alarm_in(0.1, self.update_display)
    
    def run(self):
        try:
            self.loop.run()
        finally:
            self.save_data()

def run():
    app = App()
    app.run()

if __name__ == "__main__":
    run()
