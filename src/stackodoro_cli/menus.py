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
    def __init__(self, on_set_playlist, on_music, on_previous, on_next):
        self.btn_set_playlist = MinimalButton("Set Playlist Dir", on_press=lambda _: on_set_playlist())
        self.btn_play_pause = MinimalButton("Play Music", on_press=lambda _: on_music())
        self.btn_previous = MinimalButton("Previous Track", on_press=lambda _: on_previous())
        self.btn_next = MinimalButton("Next Track", on_press=lambda _: on_next())

        self.pile = urwid.Pile([
            urwid.Text("Controls", align='center'),
            urwid.Divider(),
            self.btn_set_playlist,
            self.btn_play_pause,
            # slots for previous and next
            urwid.Divider(),
            urwid.Divider(),
        ])
        
        padded = urwid.Padding(self.pile, align='center', width=20)
        filler = urwid.Filler(padded, 'middle')
        super().__init__(filler)

    def set_play_pause_label(self, is_playing: bool):
        label = "Pause Music" if is_playing else "Play Music"
        self.btn_play_pause._label.set_text(label)

        if is_playing:
            # restore buttons
            self.pile.contents[4] = (self.btn_previous, self.pile.options())
            self.pile.contents[5] = (self.btn_next, self.pile.options())
        else:
            self.pile.contents[4] = (urwid.Divider(), self.pile.options())
            self.pile.contents[5] = (urwid.Divider(), self.pile.options())

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

class PlaylistPickerDialog(urwid.WidgetWrap):
    def __init__(self, on_apply, on_cancel, initial_dir=""):
        self.on_apply_callback = on_apply
        
        self.playlist_dir = urwid.Edit("Dir: ", initial_dir)
        
        apply_btn = MinimalButton("Apply", on_press=self.try_submit)
        cancel_btn = MinimalButton("Cancel", on_press=lambda _: on_cancel())
        
        dialog_pile = urwid.Pile([
            urwid.Text("Playlist Directory Picker (accepts mp3, wav, flac and ogg)", align='center'),
            urwid.Divider(),
            self.playlist_dir,
            urwid.Divider(),
            urwid.Columns([
                apply_btn,
                cancel_btn,
            ]),
        ])
        
        box = urwid.LineBox(urwid.Filler(dialog_pile, 'middle'))
        super().__init__(box)

    def try_submit(self, button=None):
        try:
            self.on_apply_callback(self.playlist_dir.get_edit_text())
        except ValueError:
            pass # ignore

class VolumeDisplay(urwid.WidgetWrap):
    def __init__(self, initial_volume=1.0):
        self.text_widget = urwid.Text("", align='center')
        self.update_volume(initial_volume)
        
        filler = urwid.Filler(self.text_widget, 'middle')
        super().__init__(filler)
        
    def update_volume(self, volume: float):
        bars = int(round(volume * 10))
        lines = [" Vol "]
        for i in range(10, 0, -1):
            if i <= bars:
                lines.append(" ███ ")
            else:
                lines.append(" ░░░ ")
        lines.append(f"{int(volume*100)}%".center(5))
        
        self.text_widget.set_text("\n".join(lines))
