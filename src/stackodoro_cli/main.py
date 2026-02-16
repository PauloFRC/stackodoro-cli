from .models import AppState
from .pomodoro import Pomodoro, SessionType
from .bookshelf import Bookshelf
from .presenter import display_view
from .theme import palette, MinimalButton

import urwid

class App:
    def __init__(self):
        self.state = AppState()

        # services
        self.bookshelf = Bookshelf()
        self.state.bookshelf_count = len(self.bookshelf)
        self.pomodoro = None
        
        # ASCII art display
        self.display_text = urwid.Text("", align='center', wrap='clip')
        
        # left menu - pomodoro controls
        self.btn_25_5 = MinimalButton("25+5+20", on_press=lambda btn: self.start_preset(25, 5, 20))
        self.btn_35_10 = MinimalButton("35+10+20", on_press=lambda btn: self.start_preset(35, 10, 20))
        self.btn_40_20 = MinimalButton("40+20+30", on_press=lambda btn: self.start_preset(40, 20, 30))
        self.btn_custom = MinimalButton("Custom Timer", on_press=self.show_custom_dialog)
        self.btn_quit = MinimalButton("Quit", on_press=self.quit_app)
        
        self.left_menu = urwid.Pile([
            urwid.Text("Pomodoro", align='center'),
            urwid.Divider(),
            self.btn_25_5,
            self.btn_35_10,
            self.btn_40_20,
            urwid.Divider(),
            self.btn_custom,
            urwid.Divider(),
            self.btn_quit,
        ])
                
        # right menu - other controls TODO
        self.btn_music = MinimalButton("Play Music", on_press=self.toggle_music)
        
        self.right_menu = urwid.Pile([
            urwid.Text("Controls", align='center'),
            urwid.Divider(),
            self.btn_music,
        ])
        
        self.display_box = urwid.Filler(self.display_text, 'middle')
        
        self.left_box = urwid.Filler(urwid.Padding(self.left_menu, align='center', width=20), 'middle')
        self.right_box = urwid.Filler(urwid.Padding(self.right_menu, align='center', width=20), 'middle')
        
        self.empty_left = urwid.Filler(urwid.Text(""), 'middle')
        self.empty_right = urwid.Filler(urwid.Text(""), 'middle')
        
        self.columns = urwid.Columns([
            ('weight', 1, self.left_box),
            ('weight', 3, self.display_box),
            ('weight', 1, self.right_box),
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
        self.custom_dialog_open = False
        
        self.loop.set_alarm_in(0.1, self.update_display)
    
    def _auto_hide_menus(self, loop, user_data):
        self.hide_menus()
        self._hide_alarm = None
    
    # hide menu after 5 seconds of inactivity
    def _schedule_autohide(self):
        if self._hide_alarm:
            self.loop.remove_alarm(self._hide_alarm)
        
        self._hide_alarm = self.loop.set_alarm_in(5, self._auto_hide_menus)
    
    def hide_menus(self):
        self.menus_visible = False
        self.columns.contents[0] = (self.empty_left, self.columns.options('weight', 1))
        self.columns.contents[2] = (self.empty_right, self.columns.options('weight', 1))
    
    def show_menus(self):
        self.menus_visible = True
        self.columns.contents[0] = (self.left_box, self.columns.options('weight', 1))
        self.columns.contents[2] = (self.right_box, self.columns.options('weight', 1))
    
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
    
    def show_custom_dialog(self, button=None):
        if self.custom_dialog_open:
            return
        
        self.custom_dialog_open = True
        
        self.work_edit = urwid.Edit("Work (min): ", "25")
        self.break_edit = urwid.Edit("Break (min): ", "5")
        self.big_break_edit = urwid.Edit("Big Break (min): ", "20")
        
        start_btn = MinimalButton("Start", on_press=self.start_custom_timer)
        cancel_btn = MinimalButton("Cancel", on_press=self.close_custom_dialog)
        
        dialog_pile = urwid.Pile([
            urwid.Text("Custom Timer", align='center'),
            urwid.Divider(),
            self.work_edit,
            self.break_edit,
            self.big_break_edit,
            urwid.Divider(),
            urwid.Columns([
                start_btn,
                cancel_btn,
            ]),
        ])
        
        dialog = urwid.LineBox(urwid.Filler(dialog_pile))
        overlay = urwid.Overlay(
            dialog,
            self.main_widget,
            align='center',
            width=('relative', 40),
            valign='middle',
            height=('relative', 40)
        )
        
        self.loop.widget = overlay
    
    def start_custom_timer(self, button=None):
        try:
            work = int(self.work_edit.get_edit_text())
            break_time = int(self.break_edit.get_edit_text())
            big_break = int(self.big_break_edit.get_edit_text())
            
            self.close_custom_dialog()
            self.start_preset(work, break_time, big_break)
        except ValueError:
            pass
    
    def close_custom_dialog(self, button=None):
        self.custom_dialog_open = False
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
            self.bookshelf.save()
            self.state.bookshelf_count += 1
            
        self.pomodoro.confirm_transition()
    
    def toggle_music(self, button=None):
        pass
    
    def quit_app(self, button=None):
        self.bookshelf.save()
        if self.pomodoro:
            self.pomodoro.stop()
        raise urwid.ExitMainLoop()
    
    def handle_input(self, key):
        if self.custom_dialog_open:
            if key in ('esc',):
                self.close_custom_dialog()
            elif key == 'enter':
                self.start_custom_timer()
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
        # steam logic
        pomodoro_state = self.state.pomodoro_status
        if not pomodoro_state or (not pomodoro_state.is_paused and not pomodoro_state.is_transition_pending):
            self.steam_tick_counter += 1
            if self.steam_tick_counter >= self.steam_update_threshold:
                self.state.steam_state = (self.state.steam_state + 1) % 4
                self.steam_tick_counter = 0
    
    def update_display(self, loop, user_data=None):
        self.state.bookshelf_count = len(self.bookshelf)
        self.state.bookshelf_render = self.bookshelf.render()

        if self.pomodoro:
            self.state.pomodoro_status = self.pomodoro.get_status()

        self.update_animations()

        markup_content = display_view(self.state)
        self.display_text.set_text(markup_content)
        
        loop.set_alarm_in(0.1, self.update_display)
    
    def run(self):
        try:
            self.loop.run()
        finally:
            self.bookshelf.save()

def run():
    app = App()
    app.run()

if __name__ == "__main__":
    run()
