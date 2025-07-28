# Copyright (C) 2025 APH10 Limited
# SPDX-License-Identifier: Apache-2.0
import tempfile

from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, RadioButton, RadioSet, Static

import bids.sbom
from bids.ui.display import DisplayScreen

# --- Data for Dynamic Forms ---
SPDX_FORMATS = [("JSON", "json"), ("Tag-Value", "tag"), ("YAML", "yaml")]
CYCLONEDX_FORMATS = [("JSON", "json")]


class SbomScreen(ModalScreen):

    def __init__(
        self,
        target_path,
        name=None,
        id=None,
        classes=None,
    ):
        super().__init__(name, id, classes)
        self.target_path = target_path

    def compose(self):
        with Container(id="sbom_options_container"):
            yield Label(f"Generate SBOM for: {self.target_path}")
            yield Static("SBOM Type:", classes="label")
            with RadioSet(id="sbom_type"):
                yield RadioButton("SPDX", value=True, id="sbom_spdx")
                yield RadioButton("CycloneDX", id="sbom_cyclonedx")
            yield Static("SBOM Format:", classes="label")
            with RadioSet(id="sbom_format"):
                # SPDX is the default, so populate its formats initially
                for name, value in SPDX_FORMATS:
                    yield RadioButton(name, value=name == "JSON")  # Default to JSON
            yield Static("Optional Filename:", classes="label")
            yield Input(placeholder="e.g., my-sbom.json", id="sbom_filename")
            yield Horizontal(
                Button("Generate SBOM", variant="primary", id="generate"),
                Button("Cancel", id="cancel"),
                classes="action_buttons",
            )

    def _show_sbom_format(self, event, default=True, setting=None):
        format_set = self.query_one("#sbom_format", RadioSet)
        # Find and remove all existing radio buttons
        for button in format_set.query("RadioButton"):
            button.remove()
        if event.radio_set.id == "sbom_type":
            selected_type = event.radio_set.pressed_button.label.plain
        else:
            selected_type = self.query_one(
                "#sbom_type", RadioSet
            ).pressed_button.label.plain
        formats = SPDX_FORMATS if selected_type == "SPDX" else CYCLONEDX_FORMATS
        new_buttons = []
        for name, _ in formats:
            new_buttons.append(RadioButton(name))
        format_set.mount_all(new_buttons)
        # Select the first new radio button by default
        if default and new_buttons:
            new_buttons[0].value = True
        else:
            index = event.radio_set.pressed_index
            new_buttons[index].value = True

    def on_radio_set_changed(self, event):
        """Dynamically update format options based on selected type."""
        if event.radio_set.id == "sbom_type":
            # Change of SBOM Type
            self._show_sbom_format(event)
        elif event.radio_set.id == "sbom_format":
            # Change format within SBOM Type
            selected_format = event.radio_set.pressed_button.label.plain
            self._show_sbom_format(event, default=False, setting=selected_format)

    def on_button_pressed(self, event):
        print(event.button.id)
        if event.button.id == "generate":
            self.process_sbom_generation()
        elif event.button.id == "cancel":
            self.app.pop_screen()

    def process_sbom_generation(self):
        sbom_type = self.query_one("#sbom_type", RadioSet).pressed_button.label.plain
        format = self.query_one("#sbom_format", RadioSet).pressed_button.label.plain
        formats = SPDX_FORMATS if sbom_type == "SPDX" else CYCLONEDX_FORMATS
        sbom_format = ""
        for name, value in formats:
            if name == format:
                sbom_format = value
                break
        filename = self.query_one(Input).value

        sbom_packages, sbom_relationships = bids.sbom.process_file(
            str(self.target_path)
        )
        if filename:
            output_dir = (
                self.target_path.parent
                if self.target_path.is_file()
                else self.target_path
            )
            output_path = output_dir / filename
        else:
            # Send to screen via temporary file
            bids_tempfile = tempfile.NamedTemporaryFile(prefix="bids")
            output_path = bids_tempfile.name

        bids.sbom.create_sbom(
            sbom_type,
            sbom_format,
            sbom_packages,
            sbom_relationships,
            output_file=str(output_path),
        )

        if filename:
            # Show a success message
            self.app.pop_screen()
            self.app.notify(
                f"SBOM saved to {output_path}",
                title="Success",
                severity="information",
                timeout=5,
            )
        else:
            # Display the content on a new screen
            with open(str(output_path)) as f:
                sbom_content = f.read()
                sbom_content = sbom_content.splitlines()
                self.app.push_screen(DisplayScreen(sbom_content, sbom_format))
            bids_tempfile.close()
