from .state_manager import StateManager
from .presenter import display_view
from .theme import palette, MinimalButton

import urwid
import sys
from io import StringIO

class App:
    def __init__(self):
        self.state_manager = StateManager()
        
        # ASCII art display
        self.display_text = urwid.Text("", align='center', wrap='clip')
        
        # left menu - pomodoro controls
        self.btn_25_5 = MinimalButton("25+5+20", on_press=lambda btn: self.start_preset(25, 5, 20))
        self.btn_35_10 = MinimalButton("35+10+20", on_press=lambda btn: self.start_preset(35, 10, 20))
        self.btn_40_20 = MinimalButton("40+20+40", on_press=lambda btn: self.start_preset(40, 20, 40))
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
                
        # right menu - music controls TODO
        self.btn_music = MinimalButton("Play Music", on_press=self.toggle_music)
        
        self.right_menu = urwid.Pile([
            urwid.Text("Music", align='center'),
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
        
        self.timer_running = False
        self.custom_dialog_open = False
        self.menus_visible = True

        self.loop.set_alarm_in(0.1, self.update_display)
    
    def hide_menus(self):
        self.menus_visible = False
        self.columns.contents[0] = (self.empty_left, self.columns.options('weight', 1))
        self.columns.contents[2] = (self.empty_right, self.columns.options('weight', 1))
    
    def show_menus(self):
        self.menus_visible = True
        self.columns.contents[0] = (self.left_box, self.columns.options('weight', 1))
        self.columns.contents[2] = (self.right_box, self.columns.options('weight', 1))
    
    def start_preset(self, work_minutes, break_minutes, big_break_minutes):
        self.state_manager.start_pomodoro(
            work_minutes=work_minutes,
            break_minutes=break_minutes,
            big_break_minutes=big_break_minutes,
            n_cycles=3
        )
        self.timer_running = True
        self.state_manager.is_paused = False
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
        self.state_manager.is_paused = not self.state_manager.is_paused
    
    def toggle_music(self, button=None):
        pass
    
    def quit_app(self, button=None):
        raise urwid.ExitMainLoop()
    
    def handle_input(self, key):
        if self.custom_dialog_open:
            if key in ('esc',):
                self.close_custom_dialog()
            elif key == 'enter':
                self.start_custom_timer()
            return
        
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()
        elif key == ' ':
            if self.state_manager.pomodoro:
                self.toggle_pause()
        else:
            if not self.menus_visible:
                self.show_menus()
            return key
    
    def update_display(self, loop, user_data=None):
        self.state_manager.tick()
        
        markup_content = display_view(self.state_manager)

        self.display_text.set_text(markup_content)
        
        loop.set_alarm_in(0.1, self.update_display)
    
    def run(self):
        self.loop.run()


def run():
    app = App()
    app.run()


if __name__ == "__main__":
    run()
