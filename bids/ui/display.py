# Copyright (C) 2025 APH10 Limited
# SPDX-License-Identifier: Apache-2.0

from textual.containers import Container, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static


class DisplayScreen(ModalScreen):

    def __init__(self, content, content_type, name=None, id=None, classes=None):
        super().__init__(name, id, classes)
        self.content = content
        self.content_type = content_type

    def compose(self):
        with Container(id="display_container"):
            yield Label(f"Generated Data ({self.content_type})")
            # Place the long content in its own scrollable container to allow the Close button to be always visible
            with VerticalScroll(id="display_scroller"):
                for line in self.content:
                    yield Static(line)
        yield Button("Close", variant="primary", id="close_button")

    def on_button_pressed(self, event):
        if event.button.id == "close_button":
            self.app.pop_screen()
