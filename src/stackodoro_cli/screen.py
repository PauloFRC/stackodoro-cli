import urwid

from .models import UIState, Action
from .menus import LeftMenu, RightMenu, CustomTimerDialog, PlaylistPickerDialog, VolumeDisplay
from .presenter import display_view

class MainScreen(urwid.WidgetWrap):
    def __init__(self, 
                 left_menu: LeftMenu, 
                 right_menu: RightMenu, 
                 volume_display: VolumeDisplay,
                 custom_timer_dialog: CustomTimerDialog,
                 playlist_picker_dialog: PlaylistPickerDialog
                 ):
        
        self.left_menu = left_menu
        self.right_menu = right_menu
        self.custom_timer_dialog = custom_timer_dialog
        self.playlist_picker_dialog = playlist_picker_dialog
        self.volume_display = volume_display
        self.empty_side = urwid.Filler(urwid.Text(""), 'middle')

        # center view
        self.display_text = urwid.Text("", align='center', wrap='clip')
        self.display_box = urwid.Filler(self.display_text, 'middle')

        self.overlay = None

        self.columns = urwid.Columns([
            ('weight', 1, self.left_menu),
            ('weight', 3, self.display_box),
            ('weight', 1, self.right_menu),
        ])

        self.root = urwid.WidgetPlaceholder(self.columns)
        super().__init__(self.root)

    def update(self, state: UIState):
        self.display_text.set_text(display_view(state.ascii))

        self._build_columns(state)

        self._build_dialog(state)
    
    def _build_columns(self, state: UIState):
        # left menu
        left_widget = self.left_menu if state.menu.show_menus else self.empty_side
        self.columns.contents[0] = (left_widget, self.columns.options('weight', 1))
        
        # volume update
        self.volume_display.update_volume(state.menu.volume)

        # right menu
        if state.menu.show_volume:
            self.columns.contents[2] = (self.volume_display, self.columns.options('weight', 1))
        elif state.menu.show_menus:
            self.columns.contents[2] = (self.right_menu, self.columns.options('weight', 1))
        else:
            self.columns.contents[2] = (self.empty_side, self.columns.options('weight', 1))

        # ascii view
        self.columns.contents[1] = (self.display_box, self.columns.options('weight', 3))
    
    def _build_dialog(self, state: UIState):
        if not state.menu.show_custom_timer_dialog and not state.menu.show_playlist_picker_dialog:
            self.root.original_widget = self.columns
            return
        
        if state.menu.show_custom_timer_dialog:
            dialog = self.custom_timer_dialog
        elif state.menu.show_playlist_picker_dialog:
            dialog = self.playlist_picker_dialog
        else:
            raise RuntimeError("Invalid state. This should not happen.")
        
        overlay = urwid.Overlay(
                dialog,
                self.columns,
                align="center",
                width=("relative", 40),
                valign="middle",
                height=("relative", 40),
            )
        self.root.original_widget = overlay
            