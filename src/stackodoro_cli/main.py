from .messages import get_pomodoro_session_message
from .menus import LeftMenu, RightMenu, CustomTimerDialog, PlaylistPickerDialog, VolumeDisplay
from .theme import palette
from .models import AppState
from .pomodoro import Pomodoro, SessionType
from .bookshelf import Bookshelf
from .book import Book
from .presenter import display_view
from .audio import AudioMixer, Paused, Playing, Quitting


import urwid
import json
import os
from pathlib import Path
from itertools import dropwhile

class App:
    def __init__(self):
        self.state = AppState()

        self.volume = 1.0

        # services
        self.bookshelf = Bookshelf()
        self.mixer = AudioMixer(self.volume)
        self.pomodoro = None
        
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
            on_set_playlist=self.show_playlist_picker_dialog,
            on_music=self.toggle_music
        )
        self.volume_display = VolumeDisplay(self.volume)
        
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

        # load persistent data
        self._init_storage()
        self._load_data()

        self._hide_alarm = None
        self._hide_volume_alarm = False
        self.steam_tick_counter = 0
        self.steam_update_threshold = 12
        self.menus_visible = True
        self.active_pomodoro_dialog: CustomTimerDialog | None = None
        self.active_playlist_dialog: PlaylistPickerDialog | None = None
        self._transition_sound_played = False
        self._play_shelf_completed = False

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
        
        playlist_dir = data.get('playlist_dir')
        if playlist_dir:
            self.mixer.load_playlist(playlist_dir)
        
    def save_data(self):
        data = {
            'playlist_dir': self.mixer.dir if self.mixer else None,
            'n_shelfs_completed': self.bookshelf.n_shelfs_completed,
            'books': [
                {
                    # drops starting empty lines so height is correctly calculated when reloadings
                    'ascii': list(dropwhile(lambda line: not line.strip(), book.ascii)),
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
    
    def _auto_hide_volume(self, loop, user_data):
        self.hide_volume()
        self._hide_volume_alarm = None
    
    # autohide menu after 5 seconds
    def _schedule_autohide(self):
        if self._hide_alarm:
            self.loop.remove_alarm(self._hide_alarm)
        self._hide_alarm = self.loop.set_alarm_in(5, self._auto_hide_menus)
    
    # autohide volume menu after 2 seconds
    def _schedule_autohide_volume(self):
        if self._hide_volume_alarm:
            self.loop.remove_alarm(self._hide_volume_alarm)
        self._hide_volume_alarm = self.loop.set_alarm_in(2, self._auto_hide_volume)
    
    def hide_menus(self):
        self.menus_visible = False
        self.columns.contents[0] = (self.empty_side, self.columns.options('weight', 1))
        if not self._hide_volume_alarm:
            self.columns.contents[2] = (self.empty_side, self.columns.options('weight', 1))
    
    def hide_volume(self):
        if self.menus_visible:
            self.columns.contents[2] = (self.right_menu, self.columns.options('weight', 1))
        else:  
            self.columns.contents[2] = (self.empty_side, self.columns.options('weight', 1))
    
    def show_menus(self):
        self.menus_visible = True
        self.columns.contents[0] = (self.left_menu, self.columns.options('weight', 1))
        if not self._hide_volume_alarm:
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
        if self.active_pomodoro_dialog:
            return
            
        self.active_pomodoro_dialog = CustomTimerDialog(
            on_start=self.start_custom_timer,
            on_cancel=self.close_pomodoro_dialog
        )
        
        overlay = urwid.Overlay(
            self.active_pomodoro_dialog,
            self.main_widget,
            align='center',
            width=('relative', 40),
            valign='middle',
            height=('relative', 40)
        )
        
        self.loop.widget = overlay

    # playlist dir picker dialog
    def show_playlist_picker_dialog(self):
        if self.active_playlist_dialog:
            return
        
        self.active_playlist_dialog = PlaylistPickerDialog(
            on_apply=self.set_playlist_directory,
            on_cancel=self.close_playlist_picker_dialog,
            initial_dir=self.mixer.dir if self.mixer else ""
        )

        overlay = urwid.Overlay(
            self.active_playlist_dialog,
            self.main_widget,
            align='center',
            width=('relative', 40),
            valign='middle',
            height=('relative', 40)
        )
        self.loop.widget = overlay

    def start_custom_timer(self, work, break_time, big_break):
        self.close_pomodoro_dialog()
        self.start_preset(work, break_time, big_break)
    
    def set_playlist_directory(self, dir):
        self.mixer.load_playlist(dir)
        self.close_playlist_picker_dialog()
    
    def close_pomodoro_dialog(self):
        self.active_pomodoro_dialog = None
        self.loop.widget = self.main_widget

    def close_playlist_picker_dialog(self):
        self.active_playlist_dialog = None
        self.loop.widget = self.main_widget

    def adjust_volume(self, delta):
        self._volume_show = True
        self.volume = max(0.0, min(1.0, self.volume + delta))   

        if hasattr(self.mixer, 'set_volume'):
            self.mixer.set_volume(self.volume)
        
        self.volume_display.update_volume(self.volume)
        
        self.columns.contents[2] = (self.volume_display, self.columns.options('weight', 1))
    
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
        pomodoro_status = self.pomodoro.get_status()
        mixer_state = self.mixer.state

        # resume music if it was paused and we are in work session
        if isinstance(mixer_state, Paused) and pomodoro_status.session_type == SessionType.WORK:
            self.mixer.play_playlist()
        
        # if we are no longer in WORK (meaning work finished), add a book
        if pomodoro_status.session_type != SessionType.WORK:
            self.bookshelf.add_book()
            self.save_data()
            
        self.pomodoro.confirm_transition()

    def toggle_music(self):
        if not self.mixer:
            return
        
        if isinstance(self.mixer.state, Playing):
            self.mixer.stop()
        else:
            self.mixer.play_playlist()
        # update button label to reflect new state
        try:
            self.right_menu.set_play_pause_label(isinstance(self.mixer.state, Playing))
        except Exception:
            pass
    
    def play_playlist(self):
        try:
            self.mixer.play_playlist()
        except RuntimeError as e:
            # TODO: show error in UI instead of just printing
            raise RuntimeError(f"Error playing playlist: {e}")

    def stop_playlist(self):
        self.mixer.stop()
    
    def quit_app(self):
        self.save_data()
        if self.pomodoro:
            self.pomodoro.stop()
        self.mixer.quit()
        raise urwid.ExitMainLoop()
    
    def handle_input(self, key):
        if self.active_pomodoro_dialog:
            if key == 'esc':
                self.close_pomodoro_dialog()
            elif key == 'enter':
                self.active_pomodoro_dialog.try_submit()
            return
        
        if self.active_playlist_dialog:
            if key == 'esc':
                self.close_playlist_picker_dialog()
            elif key == 'enter':
                self.active_playlist_dialog.try_submit()
            return
        
        if key in ('+', '='):
            self.adjust_volume(0.1)
            self._schedule_autohide_volume()
            return
        elif key in ('-', '_'):
            self.adjust_volume(-0.1)
            self._schedule_autohide_volume()
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

    def _handle_transition_sound(self):
        is_transitioning = self.state.pomodoro_status.is_transition_pending
                
        if is_transitioning and not self._transition_sound_played:
            ''' 
            pause music and play transition sound
            pause considers it will play again in work sessions, 
            while stop requires user to manually start music again
            '''
            self.mixer.pause()
            if self._play_shelf_completed:
                self.mixer.play_shelf_complete()
                self._play_shelf_completed = False
            else:
                self.mixer.play_session_complete()
            
            self._transition_sound_played = True
        elif not is_transitioning:
            self._transition_sound_played = False
    
    def update_display(self, loop, user_data=None):
        # mixer updates
        self.state.music_playing = self.mixer.state.track if self.mixer and isinstance(self.mixer.state, Playing) else None

        # bookshelf updates
        self.state.bookshelf_render = self.bookshelf.render()

        prev_n_shelfs_completed = self.state.n_shelfs_completed
        self.state.n_shelfs_completed = self.bookshelf.get_n_shelfs_completed()
        if self.state.n_shelfs_completed > prev_n_shelfs_completed:
            self._play_shelf_completed = True

        # pomodoro updates
        if self.pomodoro:
            self.state.pomodoro_status = self.pomodoro.get_status()
            self._handle_transition_sound()

        # animations updates
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
