import urwid
from .theme import MinimalButton

# pomodoro controls
class LeftMenu(urwid.WidgetWrap):
    def __init__(self, on_preset, on_custom, on_quit):
        btn_25_5 = MinimalButton("25+5+20", on_press=lambda _: on_preset(25, 5, 20))
        btn_35_10 = MinimalButton("35+10+20", on_press=lambda _: on_preset(35, 10, 20))
        btn_40_20 = MinimalButton("40+20+30", on_press=lambda _: on_preset(40, 20, 30))
        btn_custom = MinimalButton("Custom Timer", on_press=lambda _: on_custom())
        btn_quit = MinimalButton("Quit", on_press=lambda _: on_quit())
        
        pile = urwid.Pile([
            urwid.Text("Pomodoro", align='center'),
            urwid.Divider(),
            btn_25_5,
            btn_35_10,
            btn_40_20,
            urwid.Divider(),
            btn_custom,
            urwid.Divider(),
            btn_quit,
        ])
        
        padded = urwid.Padding(pile, align='center', width=20)
        filler = urwid.Filler(padded, 'middle')
        super().__init__(filler)

# other controls
class RightMenu(urwid.WidgetWrap):
    def __init__(self, on_music):
        btn_music = MinimalButton("Play Music", on_press=lambda _: on_music())
        
        pile = urwid.Pile([
            urwid.Text("Controls", align='center'),
            urwid.Divider(),
            btn_music,
        ])
        
        padded = urwid.Padding(pile, align='center', width=20)
        filler = urwid.Filler(padded, 'middle')
        super().__init__(filler)


class CustomTimerDialog(urwid.WidgetWrap):
    def __init__(self, on_start, on_cancel):
        self.on_start_callback = on_start
        
        self.work_edit = urwid.Edit("Work (min): ", "25")
        self.break_edit = urwid.Edit("Break (min): ", "5")
        self.big_break_edit = urwid.Edit("Big Break (min): ", "20")
        
        start_btn = MinimalButton("Start", on_press=self.try_submit)
        cancel_btn = MinimalButton("Cancel", on_press=lambda _: on_cancel())
        
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
        
        box = urwid.LineBox(urwid.Filler(dialog_pile, 'middle'))
        super().__init__(box)

    def try_submit(self, button=None):
        try:
            work = int(self.work_edit.get_edit_text())
            break_time = int(self.break_edit.get_edit_text())
            big_break = int(self.big_break_edit.get_edit_text())
            self.on_start_callback(work, break_time, big_break)
        except ValueError:
            pass # ignore
