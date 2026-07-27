import urwid
import time

from .menus import LeftMenu, RightMenu, CustomTimerDialog, PlaylistPickerDialog, VolumeDisplay
from .theme import palette
from .models import (UIState, AppSnapshot, Action, UIElement, Tick, DisplayError, SetVisible, 
                     AdjustVolume, PlaySessionCompletedSound, PlayShelfCompletedSound, PlaySessionStartSound, 
                     PlayPlaylist, StopPlaylist, PausePlaylist, ToggleMusic, PreviousTrack, NextTrack, TogglePause, 
                     SkipSession, StartTimer, SetPlaylistDir, Quit)
from .pomodoro import Pomodoro, SessionType
from .bookshelf import Bookshelf
from .audio import AudioMixer, Paused, Playing
from .storage import storage_service
from .screen import MainScreen

class App:
    def __init__(self):
        self.state = UIState()
        self.volume = 1.0

        # services
        self.bookshelf = Bookshelf()
        self.mixer = AudioMixer(self.volume)
        self.pomodoro = None

        # load persistent data
        self.load_data()
        
        self.start_time = time.time()
        
        # screen
        self.left_menu = LeftMenu(on_action=self.handle)
        self.right_menu = RightMenu(on_action=self.handle)
        self.volume_display = VolumeDisplay(self.volume)
        
        self.main_screen = MainScreen(
            left_menu=self.left_menu,
            right_menu=self.right_menu,
            volume_display=self.volume_display,
            custom_timer_dialog=CustomTimerDialog(on_action=self.handle),
            playlist_picker_dialog=PlaylistPickerDialog(
                on_action=self.handle,
                initial_dir=self.state.menu.current_playlist_dir
            )
        )
        self.loop = urwid.MainLoop(
            self.main_screen, 
            palette=palette, 
            unhandled_input=self.handle_input
        )

        self.steam_tick_counter = 0
        self.steam_update_threshold = 12
        self._transition_sound_played = False
        self.play_shelf_completed = False

        # for now, plays session complete effect on init
        self.handle(PlaySessionCompletedSound())
        
        self.loop.set_alarm_in(0.1, self.update_display)
        
    def load_data(self):
        snapshot = storage_service.load_state()
        
        self.bookshelf.load_books(snapshot.books, snapshot.n_shelfs_completed)
        self.state.ascii.n_shelfs_completed = snapshot.n_shelfs_completed
        if snapshot.playlist_dir:
            self.mixer.load_playlist(snapshot.playlist_dir) #TODO Change
            self.state.menu.current_playlist_dir = snapshot.playlist_dir
        
    def save_data(self):
        snapshot = AppSnapshot(
            playlist_dir=self.state.menu.current_playlist_dir,
            n_shelfs_completed=self.bookshelf.n_shelfs_completed,
            books=self.bookshelf.get_books()
        )        
        storage_service.save_state(snapshot)

    def handle(self, action: Action):
        match action:
            case Tick():
                self.tick()
            case DisplayError(error_msg=error_msg):
                self.state.menu.error_msg = error_msg
                self.set_visibility(UIElement.ERROR_MSG, True)
            case SetVisible(element=element, visible=visible):
                self.set_visibility(element, visible)
            case AdjustVolume(delta=delta):
                volume = max(0.0, min(1.0, self.state.menu.volume + delta))
                self.state.menu.volume = volume
                self.mixer.set_volume(volume) # TODO see if this can be optimized
                self.set_visibility(UIElement.VOLUME, True)
            case PlaySessionCompletedSound():
                self.mixer.play_session_complete()
            case PlayShelfCompletedSound():
                self.mixer.play_shelf_complete()
                self.play_shelf_completed = False
            case PlaySessionStartSound():
                self.mixer.play_session_start()
            case PlayPlaylist():
                self.play_playlist()
            case StopPlaylist():
                self.mixer.stop()
            case PausePlaylist():
                self.mixer.pause()
            case PreviousTrack():
                self.mixer.previous_track()
            case NextTrack():
                self.mixer.skip_track()
            case ToggleMusic():
                self.toggle_music()
            case SkipSession():
                self.skip_session()
            case TogglePause():
                self.toggle_pause()
            case StartTimer(work_minutes=work, break_minutes=break_time, big_break_minutes=big_break):
                self.hide_all_dialogs()
                self.start_preset(work, break_time, big_break)
                self.mixer.play_session_start()
            case SetPlaylistDir(directory=dir):
                self.set_playlist_directory(dir)
            case Quit():
                self.quit_app()
            
    def tick(self):
        # mixer updates
        self.state.ascii.music_playing = self.mixer.state.track if self.mixer and isinstance(self.mixer.state, Playing) else None

        # bookshelf updates
        self.state.ascii.bookshelf_render = self.bookshelf.render()

        prev_n_shelfs_completed = self.state.ascii.n_shelfs_completed
        self.state.ascii.n_shelfs_completed = self.bookshelf.get_n_shelfs_completed()
        if self.state.ascii.n_shelfs_completed > prev_n_shelfs_completed:
            self.play_shelf_completed = True

        # pomodoro updates
        if self.pomodoro:
            self.state.ascii.pomodoro_status = self.pomodoro.get_status()
            self.handle_transition_sound()
        
        # uptime updates
        self.state.ascii.uptime_seconds = int(time.time() - self.start_time)

        # animation updates
        self.tick_animations()

        # update screen
        self.main_screen.update(self.state)

    
    def tick_animations(self):
        pomodoro_state = self.state.ascii.pomodoro_status

        # update steam
        if not pomodoro_state or (not pomodoro_state.is_paused and not pomodoro_state.is_transition_pending):
            self.steam_tick_counter += 1
            if self.steam_tick_counter >= self.steam_update_threshold:
                self.state.ascii.steam_state = (self.state.ascii.steam_state + 1) % 4
                self.steam_tick_counter = 0

    def set_visibility(self, element: UIElement, visible: bool):
        match element:
            case UIElement.MENUS:
                self.state.menu.show_menus = visible
                if visible and self.pomodoro:
                    self.schedule_autohide(element, 5)
            case UIElement.VOLUME:
                self.state.menu.show_volume = visible
                if visible:
                    self.schedule_autohide(element, 3)
            case UIElement.CUSTOM_TIMER_DIALOG:
                self.state.menu.show_custom_timer_dialog = visible
            case UIElement.PLAYLIST_PICKER_DIALOG:
                self.state.menu.show_playlist_picker_dialog = visible
            case UIElement.ERROR_MSG:
                if not visible:
                    self.state.menu.error_msg = None
                else:
                    self.schedule_autohide(UIElement.ERROR_MSG, 8)

    def schedule_autohide(self, element: UIElement, seconds: int):
        alarm_key = f'_hide_{element.name.lower()}_alarm'
        
        if hasattr(self, alarm_key) and getattr(self, alarm_key):
            self.loop.remove_alarm(getattr(self, alarm_key))
        
        alarm = self.loop.set_alarm_in(
            seconds, 
            lambda *_: self.set_visibility(element, False)
        )
        setattr(self, alarm_key, alarm)        

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
        self.set_visibility(UIElement.MENUS, False)
    
    def set_playlist_directory(self, dir):
        self.set_visibility(UIElement.PLAYLIST_PICKER_DIALOG, False)
        self.mixer.load_playlist(dir)
        self.save_data()

    def play_playlist(self):
        try:
            self.mixer.play_playlist()
        except Exception as e:
            self.handle(DisplayError(e))
    
    def quit_app(self):
        self.save_data()
        if self.pomodoro:
            self.pomodoro.stop()
        self.mixer.quit()
        raise urwid.ExitMainLoop()
    
    def skip_session(self):
        if not self.pomodoro:
            return

        self.handle_transition(skip=True)

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

    def handle_transition(self, skip=False):
        if not self.pomodoro:
            return

        pomodoro_status = self.pomodoro.get_status()
        mixer_state = self.mixer.state

        # play session start soumd
        self.handle(PlaySessionStartSound())

        # resume music if it was paused and we are in work session
        if isinstance(mixer_state, Paused) and pomodoro_status.session_type == SessionType.WORK:
            self.handle(PlayPlaylist())
        
        # if we are no longer in WORK (meaning work finished), add a book if we didnt skip
        if pomodoro_status.session_type != SessionType.WORK and not skip:
            self.bookshelf.add_book()
            self.save_data()
            
        self.pomodoro.confirm_transition(skip=skip)
    
    def hide_all_dialogs(self):
        self.set_visibility(UIElement.CUSTOM_TIMER_DIALOG, False)
        self.set_visibility(UIElement.PLAYLIST_PICKER_DIALOG, False)

    def toggle_music(self):
        if not self.mixer:
            return
        
        if isinstance(self.mixer.state, Playing):
            self.handle(StopPlaylist())
        else:
            self.handle(PlayPlaylist())
        # update button label to reflect new state
        try:
            self.right_menu.set_play_pause_label(isinstance(self.mixer.state, Playing))
        except Exception as e:
            self.handle(DisplayError(e))
    
    def handle_input(self, key):
        if self.state.menu.show_custom_timer_dialog:
            if key == 'esc':
                self.handle(SetVisible(element=UIElement.CUSTOM_TIMER_DIALOG, visible=False))
            elif key == 'enter':
                self.main_screen.custom_timer_dialog.try_submit()
            return
        
        if self.state.menu.show_playlist_picker_dialog:
            if key == 'esc':
                self.handle(SetVisible(element=UIElement.PLAYLIST_PICKER_DIALOG, visible=False))
            elif key == 'enter':
                self.main_screen.playlist_picker_dialog.try_submit()
            return

        pomodoro_status = self.state.ascii.pomodoro_status
        if pomodoro_status and pomodoro_status.is_paused:
            if key == 'esc':
                self.handle(TogglePause())
            elif key == ' ':
                self.handle(SkipSession())
        
        if key in ('+', '='):
            self.handle(AdjustVolume(delta=0.1))
            return
        elif key in ('-', '_'):
            self.handle(AdjustVolume(delta=-0.1))
            return
        
        if key in ('q', 'Q'):
            self.handle(Quit())
            return
        elif key == ' ':
            if self.pomodoro:
                self.handle(TogglePause())
        else:
            if not self.state.menu.show_menus:
                self.handle(SetVisible(element=UIElement.MENUS, visible=True))
            return key

    def handle_transition_sound(self):
        is_transitioning = self.state.ascii.pomodoro_status.is_transition_pending
                
        if is_transitioning and not self._transition_sound_played:
            ''' 
            pause music and play transition sound
            pause considers it will play again in work sessions, 
            while stop requires user to manually start music again
            '''
            self.handle(StopPlaylist())
            if self.play_shelf_completed:
                self.handle(PlayShelfCompletedSound())
            else:
                self.handle(PlaySessionCompletedSound())
            
            self._transition_sound_played = True
        elif not is_transitioning:
            self._transition_sound_played = False
    
    def update_display(self, loop, user_data=None):
        self.handle(Tick())
        
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
