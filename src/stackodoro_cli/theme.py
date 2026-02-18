import urwid

palette = [
     # unfocused button
    ('minimal_button', 'light gray', ''),
    # focused button
     ('minimal_button_focus', 'black,bold', 'light gray'),
    # object colors
    ('table_color', 'yellow', ''),
    ('steam_color', 'white,bold', ''),
    ('mug_color', 'white,bold', ''),
    ('clock_color', 'white', ''),
    ('timer_color', 'white,bold', ''),
    ('notebook_color', 'light green', ''),
    ('sign_color', 'brown', ''),
    ('sign_text_color', 'white,bold', ''),
    ('shelf_color', 'light gray', ''),
    # info colors
    ('music_color', 'light cyan', ''),
    ('session_color', 'light magenta,bold', ''),
    # book colors
    ('book_color_1', 'dark blue', ''),
    ('book_color_2', 'dark green', ''),
    ('book_color_3', 'dark red', ''),
]

class SelectableText(urwid.Text):
    def selectable(self):
        return True
    def keypress(self, size, key):
        return key

class MinimalButton(urwid.Button):
    def __init__(self, label, on_press=None):
        super().__init__("")        
        self._label = SelectableText(label, align='center')        
        self._w = urwid.AttrMap(self._label, 'minimal_button', 'minimal_button_focus')        
        if on_press:
            urwid.connect_signal(self, 'click', on_press)
    
    def keypress(self, size, key):
        if key == ' ':
            return key
        return super().keypress(size, key)
    