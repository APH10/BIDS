# Copyright (C) 2025 APH10 Limited
# SPDX-License-Identifier: Apache-2.0

import tempfile

from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static

from bids.analyser import BIDSAnalyser
from bids.output import BIDSOutput
from bids.ui.display import DisplayScreen


class AnalyseScreen(ModalScreen):
    """A modal screen for selecting analysis options."""

    def __init__(
        self,
        target_path,
        name=None,
        id=None,
        classes=None,
    ):
        super().__init__(name, id, classes)
        self.target_path = target_path
        self._analysis_output_content = None

    def compose(self):
        with Container(id="analyse_options_container"):
            yield Label(f"Analyse: {self.target_path.name}")
            yield Static("Optional Description:", classes="label")
            yield Input(placeholder="e.g., Audit application", id="description_input")
            yield Static("Optional Library Path (comma-separated):", classes="label")
            yield Input(
                placeholder="e.g., /usr/lib/mylibs,./project_libs",
                id="library_path_input",
            )
            yield Static("Optional Output Filename:", classes="label")
            yield Input(
                placeholder="Leave empty to display", id="output_filename_input"
            )
            with Horizontal(id="analyse_buttons"):
                yield Button(
                    "Run Analysis", variant="primary", id="run_analysis_button"
                )
                yield Button("Cancel", id="cancel_button")

    def on_button_pressed(self, event):
        if event.button.id == "run_analysis_button":
            self.run_analysis()
        elif event.button.id == "cancel_button":
            self.app.pop_screen()  # Go back to MainScreen

    def run_analysis(self):
        description = self.query_one("#description_input", Input).value.strip()
        library_paths_str = self.query_one("#library_path_input", Input).value.strip()
        output_filename = self.query_one("#output_filename_input", Input).value.strip()
        options = {
            "dependency": False,
            "symbol": False,
            "callgraph": False,
            "detect_version": False,
        }
        analyser = BIDSAnalyser(options=options, description=description)
        generate_output = True
        try:
            analyser.analyse(str(self.target_path))
        except TypeError:
            self.app.notify(
                "Only ELF files can be analysed.",
                title="Error Processing File",
                severity="error",
            )
            generate_output = False
        except FileNotFoundError:
            self.app.notify(
                f"{self.target_path} not found.",
                title="Error Processing File",
                severity="error",
            )
            generate_output = False
        # Only if we haven't had an error
        if generate_output:
            output = BIDSOutput(
                library_path=library_paths_str,
                detect_version=False,
            )
            output.create_metadata(analyser.get_file_data())
            output.create_components(
                analyser.get_dependencies(),
                analyser.get_global_symbols(),
                analyser.get_callgraph(),
                local=analyser.get_local_symbols(),
            )
            if output_filename:
                # Save to a file
                output.generate_output(output_filename)
                self.app.pop_screen()
                self.app.notify(
                    f"Analysis report saved to '{output_filename}",
                    title="Success",
                    severity="information",
                )
            else:
                # Display output on screen
                self.app.pop_screen()
                # Send to screen via temporary file
                bids_tempfile = tempfile.NamedTemporaryFile(prefix="bids")
                output_path = bids_tempfile.name
                output.generate_output(output_path)
                with open(str(output_path)) as f:
                    analysis_content = f.read()
                    analysis_content = analysis_content.splitlines()
                    self.app.push_screen(
                        DisplayScreen(analysis_content, "Analysis Report")
                    )
                bids_tempfile.close()
        else:
            self.app.pop_screen()
