# Copyright (C) 2025 APH10 Limited
# SPDX-License-Identifier: Apache-2.0

import os
from pathlib import Path
import json  # For dummy SBOM generation

from textual.app import App, ComposeResult, Notification
from textual.containers import Container, VerticalScroll, Horizontal, Center
from textual.reactive import var
from textual.screen import Screen, ModalScreen
from textual.widgets import Button, Checkbox, DirectoryTree, Footer, Header, Static, RadioSet, RadioButton, Input, Label, Pretty

import bids.sbom

# --- Data for Dynamic Forms ---
SPDX_FORMATS = [("JSON", "json"), ("Tag-Value", "tag"), ("YAML", "yaml")]
CYCLONEDX_FORMATS = [("JSON", "json")]


class DisplayScreen(ModalScreen):
    """A modal screen to display text content, like an SBOM."""

    def __init__(self, content: str, content_type: str, name: str | None = None, id: str | None = None, classes: str | None = None) -> None:
        super().__init__(name, id, classes)
        self.content = content
        self.content_type = content_type

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="display_container"):
            yield Label(f"Generated SBOM ({self.content_type})")
            yield Pretty(self.content, id="display_content")
            yield Button("Close", variant="primary", id="close_button")
            yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close_button":
            self.app.pop_screen()
        elif event.button.id == "cancel":
            self.app.pop_screen()

class SaveAsScreen(ModalScreen[Path]): # ModalScreen[Path] indicates it returns a Path
    """A modal screen to allow the user to select a directory and filename for saving."""

    DEFAULT_CSS = """
    SaveAsScreen {
        align: center middle;
    }
    #save_as_dialog {
        width: 80%;
        height: 80%;
        background: $panel;
        border: thick $accent;
        padding: 2;
    }
    #save_as_dialog DirectoryTree {
        border: round $surface-darken-1;
        margin-bottom: 1;
        height: 1fr; /* Takes up available vertical space */
    }
    #filename_input_container {
        height: auto;
    }
    #filename_input_container Label {
        width: auto;
        margin-right: 1;
    }

    #save_as_buttons {
        height: auto;
        margin-top: 1;
        align-horizontal: center;
    }
    #save_as_buttons Button {
        margin-left: 1;
        margin-right: 1;
    }
    """

    def __init__(self, initial_path: Path, suggested_filename: str = "", name: str | None = None, id: str | None = None, classes: str | None = None) -> None:
        super().__init__(name, id, classes)
        self.selected_directory: Path = initial_path.parent if initial_path.is_file() else initial_path
        self.suggested_filename = suggested_filename

    def compose(self) -> ComposeResult:
        with Container(id="save_as_dialog"):
            yield Label("Select Save Location and Filename")
            with VerticalScroll(): # Use VerticalScroll for the DirectoryTree if it gets too large
                yield DirectoryTree(self.selected_directory, id="directory_tree") # Start from initial path
            with Horizontal(id="filename_input_container"):
                yield Label("Filename:")
                yield Input(value=self.suggested_filename, placeholder="Enter filename", id="filename_input")
            with Horizontal(id="save_as_buttons"):
                yield Button("Save", variant="primary", id="save_button")
                yield Button("Cancel", id="cancel_button")

    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        # Update the selected directory when a new directory is clicked
        self.selected_directory = event.path
        # Optionally, update the filename input if you want it to reflect the directory name
        # self.query_one("#filename_input", Input).value = event.path.name # Not usually desired for save dialog

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save_button":
            filename_input = self.query_one("#filename_input", Input)
            filename = filename_input.value.strip()

            if not filename:
                self.app.notify("Please enter a filename.", severity="warning")
                return
            # Combine the selected directory and the entered filename
            final_path = self.selected_directory / filename
            self.dismiss(final_path) # Dismiss the modal, returning the chosen path
        elif event.button.id == "cancel_button":
            self.dismiss(None) # Dismiss, returning None to indicate cancellation

class SbomScreen(ModalScreen):
    """A modal screen for selecting SBOM generation options."""

    def __init__(self, target_path: Path, name: str | None = None, id: str | None = None, classes: str | None = None) -> None:
        super().__init__(name, id, classes)
        self.target_path = target_path

    def compose(self) -> ComposeResult:
        with Container(id="sbom_options_container"):
            yield Label(f"Generate SBOM for: {self.target_path}")
            yield Static("SBOM Type:", classes="label")
            with RadioSet(id="sbom_type"):
                yield RadioButton("SPDX", value=True)
                yield RadioButton("CycloneDX")

            yield Static("SBOM Format:", classes="label")
            with RadioSet(id="sbom_format"):
                # SPDX is the default, so populate its formats initially
                for name, value in SPDX_FORMATS:
                    yield RadioButton(name, value=name=="JSON") # Default to JSON

            yield Static("Optional Filename:", classes="label")
            yield Input(placeholder="e.g., my-sbom.json", id="sbom_filename")
            yield Button("Generate SBOM", variant="primary", id="generate")
            yield Button("Cancel", variant="primary", id="cancel")
            #yield Horizontal(
            #    Button("Generate SBOM", variant="primary", id="generate"),
            #    Button("Cancel", variant="primary", id="cancel"),
            #    classes="action_buttons"
            #)

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Dynamically update format options based on selected type."""
        if event.radio_set.id == "sbom_type":
            format_set = self.query_one("#sbom_format", RadioSet)
            # Find and remove all existing radio buttons
            for button in format_set.query("RadioButton"):
                button.remove()
            selected_type = event.radio_set.pressed_button.label.plain
            formats = SPDX_FORMATS if selected_type == "SPDX" else CYCLONEDX_FORMATS
            new_buttons = []
            for name, _ in formats:
                new_buttons.append(RadioButton(name))
            format_set.mount_all(new_buttons)
            # Select the first new radio button by default
            if new_buttons:
                new_buttons[0].value = True

    def on_button_pressed(self, event: Button.Pressed) -> None:
        print (event.button.id)
        if event.button.id == "generate":
            self.process_sbom_generation()
        elif event.button.id == "cancel":
            self.app.pop_screen()

    def process_sbom_generation(self):
        """Gather options, call backend, and display/save result."""
        sbom_type = self.query_one("#sbom_type", RadioSet).pressed_button.label.plain
        sbom_format = self.query_one("#sbom_format", RadioSet).pressed_button.label.plain
        filename = self.query_one(Input).value

        # Determine a sensible default filename
        default_filename = f"sbom_{self.target_path.stem}.{sbom_format.lower()}"

        # Push the SaveAsScreen instead of directly saving or displaying
        output_file = self.app.push_screen(
                SaveAsScreen(initial_path=self.target_path, suggested_filename=default_filename),
        )

        sbom_packages, sbom_relationships = bids.sbom.process_file(str(self.target_path), "binary")
        if filename:
            output_dir = self.target_path.parent if self.target_path.is_file() else self.target_path
            output_path = output_dir / filename
        else:
            output_path = ""

        sbom_content = bids.sbom.create_sbom(sbom_type, sbom_format, sbom_packages, sbom_relationships, output_file = str(output_path))

        if filename:
            # Exit SbomScreen and show a success message on MainScreen
            self.app.pop_screen()
            self.app.notify(f"SBOM saved to {output_path}", title="Success", severity="information", timeout=5)
        else:
            # Display the content on a new screen
            self.app.push_screen(DisplayScreen(sbom_content, sbom_format))

class AnalyseScreen(ModalScreen):
    """A modal screen for selecting analysis options."""

    DEFAULT_CSS = """
    AnalyseScreen {
        align: center middle;
    }
    #analyse_options_container {
        width: 70%;
        height: auto;
        max-height: 85%;
        background: $panel;
        border: thick $primary;
        padding: 2;
    }
    #analyse_options_container Label {
        margin-top: 1;
        margin-bottom: 0;
        color: $text-muted;
    }
    #analyse_options_container Input {
        margin-bottom: 1;
    }
    #analyse_buttons {
        margin-top: 2;
        align-horizontal: center;
    }
    #analyse_buttons Button {
        margin-left: 1;
        margin-right: 1;
    }
    """

    def __init__(self, target_path: Path, name: str | None = None, id: str | None = None, classes: str | None = None) -> None:
        super().__init__(name, id, classes)
        self.target_path = target_path
        self._analysis_output_content: str | None = None # To store output before saving/displaying

    def compose(self) -> ComposeResult:
        with Container(id="analyse_options_container"):
            yield Label(f"Analyse: {self.target_path.name}")

            yield Static("Optional Description:", classes="label")
            yield Input(placeholder="e.g., Initial security audit", id="description_input")

            yield Static("Optional Library Path (comma-separated):", classes="label")
            yield Input(placeholder="e.g., /usr/lib/mylibs,./project_libs", id="library_path_input")

            yield Static("Optional Output Filename:", classes="label")
            yield Input(placeholder="Leave empty to display", id="output_filename_input")

            with Horizontal(id="analyse_buttons"):
                yield Button("Run Analysis", variant="primary", id="run_analysis_button")
                yield Button("Cancel", id="cancel_button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run_analysis_button":
            self.run_analysis()
        elif event.button.id == "cancel_button":
            self.app.pop_screen() # Go back to MainScreen

    def run_analysis(self) -> None:
        description = self.query_one("#description_input", Input).value.strip()
        library_paths_str = self.query_one("#library_path_input", Input).value.strip()
        output_filename = self.query_one("#output_filename_input", Input).value.strip()

        library_paths = [Path(p.strip()) for p in library_paths_str.split(',') if p.strip()]

        # --- TODO: Replace with your actual analysis function ---
        # For now, a dummy analysis result
        analysis_report_data = {
            "target": str(self.target_path),
            "description": description if description else "No description provided",
            "library_paths": [str(p) for p in library_paths] if library_paths else "None",
            "timestamp": "2025-07-08T16:30:00Z",
            "findings": [
                {"id": "F001", "severity": "High", "description": "Example buffer overflow vulnerability"},
                {"id": "F002", "severity": "Medium", "description": "Unused dependency found"},
            ],
            "summary": "Dummy analysis completed."
        }
        self._analysis_output_content = json.dumps(analysis_report_data, indent=2)
        # --- END TODO ---

        if output_filename:
            # Use the existing SaveAsScreen logic for output file
            # We'll pass the analysis output to it later via a callback
            default_output_path = self.target_path.parent / output_filename
            self.app.push_screen(
                SaveAsScreen(initial_path=default_output_path, suggested_filename=output_filename),
                self._handle_analysis_save_result # New callback for analysis output
            )
        else:
            # Display output on screen
            self.app.pop_screen()
            self.app.push_screen(DisplayScreen(self._analysis_output_content, "Analysis Report"))

    def _handle_analysis_save_result(self, selected_path: Path | None) -> None:
        """Callback for SaveAsScreen when saving analysis report."""
        self.app.pop_screen() # Pop the AnalyseScreen that pushed SaveAsScreen

        if selected_path is None:
            self.app.notify("Analysis report save cancelled.", severity="information")
            return

        if self._analysis_output_content:
            try:
                with open(selected_path, "w") as f:
                    f.write(self._analysis_output_content)
                self.app.notify(f"Analysis report saved to '{selected_path.name}'", title="Success", severity="information")
            except IOError as e:
                self.app.notify(f"Failed to save analysis report:\n{e}", title="Error Saving File", severity="error")
        else:
            self.app.notify("No analysis content to save.", severity="warning")

class QueryResultScreen(Screen):
    """A screen to display query results with pagination."""

    DEFAULT_CSS = """
    QueryResultScreen {
        layout: vertical;
    }
    #results_container {
        margin: 1;
        padding: 1;
    }
    #pagination_controls {
        height: auto;
        dock: bottom;
        background: $surface-darken-1;
        padding: 0 1;
        align-horizontal: center;
    }
    #pagination_controls Button, #pagination_controls Input, #pagination_controls Label {
        margin: 0 1;
    }
    #page_input {
        width: 6; /* Small width for page number input */
        text-align: center;
    }
    .result_item {
        margin-bottom: 1;
    }

    .result_item Static {
        margin-left: 2;
    }
    """

    results: list[dict] # Store all results
    page_size: int = 10
    current_page: int = 0 

    def __init__(self, results: list[dict], search_term: str, page_size: int = 10, verbose: bool = False,
                 name: str | None = None, id: str | None = None, classes: str | None = None) -> None:
        super().__init__(name, id, classes)
        self.results = results
        self.search_term = search_term
        self.page_size = page_size
        self.verbose = verbose
        self.current_page = 0 # Start at the first page

    def compose(self) -> ComposeResult:
        yield Header(name=f"Query Results for: '{self.search_term}'")
        with VerticalScroll(id="results_container"):
            # Results will be rendered here dynamically
            yield Static("No results to display yet.", id="no_results_message") # Hidden if results exist
        with Horizontal(id="pagination_controls"):
            yield Button("First", id="first_page_button", disabled=True)
            yield Button("Previous", id="prev_page_button", disabled=True)
            yield Label("Page:")
            yield Input("1", id="page_input", classes="small_input")
            yield Label(f"of {self.total_pages}")
            yield Button("Next", id="next_page_button", disabled=True)
            yield Button("Last", id="last_page_button", disabled=True)
            yield Button("Go", id="go_page_button")
        yield Footer()

    @property
    def total_pages(self) -> int:
        if not self.results:
            return 1
        return (len(self.results) + self.page_size - 1) // self.page_size

    def on_mount(self) -> None:
        self.display_current_page()

    def display_current_page(self) -> None:
        results_container = self.query_one("#results_container", VerticalScroll)
        # TODO
        # results_container.clear() # Clear existing results

        if not self.results:
            results_container.add_component(Static("No results found for this query.", id="no_results_message"))
            self._update_pagination_buttons()
            self.query_one("#page_input", Input).value = "1"
            self.query_one(Label, f"of {self.total_pages}").update(f"of {self.total_pages}") # Update total pages label
            return

        start_index = self.current_page * self.page_size
        end_index = min(start_index + self.page_size, len(self.results))
        current_page_results = self.results[start_index:end_index]

        if not current_page_results:
            # This case might happen if current_page is out of bounds
            self.current_page = 0
            self.display_current_page() # Recurse to first page
            return

        for i, result in enumerate(current_page_results):
            # Display each result as a Static or Pretty widget
            # You'll need to format `result` into a displayable string
            result_text = f"Result {start_index + i + 1}:\n"
            if self.verbose:
                result_text += json.dumps(result, indent=2) # Pretty print full result
            else:
                # Example: display specific fields
                result_text += f"  Name: {result.get('name', 'N/A')}\n"
                result_text += f"  Type: {result.get('type', 'N/A')}\n"
                result_text += f"  Path: {result.get('path', 'N/A').split('/')[-1]}\n" # Just filename for brevity
                # Add more fields as needed

            results_container.add_component(Static(result_text, classes="result_item"))

        self._update_pagination_buttons()
        self.query_one("#page_input", Input).value = str(self.current_page + 1) # Update input field
        self.query_one(Label, f"of {self.total_pages}").update(f"of {self.total_pages}") # Update total pages label


    def _update_pagination_buttons(self) -> None:
        self.query_one("#first_page_button", Button).disabled = self.current_page == 0
        self.query_one("#prev_page_button", Button).disabled = self.current_page == 0
        self.query_one("#next_page_button", Button).disabled = self.current_page >= self.total_pages - 1
        self.query_one("#last_page_button", Button).disabled = self.current_page >= self.total_pages - 1

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "prev_page_button":
            if self.current_page > 0:
                self.current_page -= 1
                self.display_current_page()
        elif event.button.id == "next_page_button":
            if self.current_page < self.total_pages - 1:
                self.current_page += 1
                self.display_current_page()
        elif event.button.id == "first_page_button":
            self.current_page = 0
            self.display_current_page()
        elif event.button.id == "last_page_button":
            self.current_page = self.total_pages - 1
            self.display_current_page()
        elif event.button.id == "go_page_button":
            try:
                page_num_input = self.query_one("#page_input", Input).value
                target_page = int(page_num_input) - 1 # Convert to 0-indexed
                if 0 <= target_page < self.total_pages:
                    self.current_page = target_page
                    self.display_current_page()
                else:
                    self.app.notify(f"Page number out of range (1-{self.total_pages}).", severity="warning")
            except ValueError:
                self.app.notify("Invalid page number.", severity="error")

    # Add bindings to go back to MainScreen
    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
    ]
    
class QueryScreen(ModalScreen): # Could be a regular Screen too
    """A modal screen for entering database query parameters."""

    DEFAULT_CSS = """
    QueryScreen {
        align: center middle;
    }
    #query_options_container {
        width: 60%;
        height: auto;
        max-height: 70%;
        background: $panel;
        border: thick $success;
        padding: 2;
    }
    #query_options_container Label {
        margin-top: 1;
        margin-bottom: 0;
        color: $text-muted;
    }
    #query_options_container Input {
        margin-bottom: 1;
    }
    #query_options_container Checkbox {
        margin-bottom: 1;
    }
    #query_buttons {
        margin-top: 2;
        align-horizontal: center;
    }
    #query_buttons Button {
        margin-left: 1;
        margin-right: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="query_options_container"):
            yield Label("Database Query")

            yield Static("Search Term:", classes="label")
            yield Input(placeholder="e.g., 'vulnerability', 'libc', 'CVE-2023-...", id="search_term_input")

            yield Static("Number of Results (default 10):", classes="label")
            yield Input("10", placeholder="e.g., 50", id="num_results_input")

            yield Checkbox("Verbose Reporting", id="verbose_checkbox")

            with Horizontal(id="query_buttons"):
                yield Button("Run Query", variant="primary", id="run_query_button")
                yield Button("Cancel", id="cancel_button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run_query_button":
            self.run_query()
        elif event.button.id == "cancel_button":
            self.app.pop_screen() # Go back to MainScreen

    def run_query(self) -> None:
        search_term = self.query_one("#search_term_input", Input).value.strip()
        num_results_str = self.query_one("#num_results_input", Input).value.strip()
        verbose = self.query_one("#verbose_checkbox", Checkbox).value

        if not search_term:
            self.app.notify("Please enter a search term.", severity="warning")
            return

        try:
            num_results = int(num_results_str) if num_results_str else 10
            if num_results <= 0:
                self.app.notify("Number of results must be positive.", severity="warning")
                return
        except ValueError:
            self.app.notify("Invalid number of results.", severity="error")
            return

        # --- TODO: Replace with your actual database query logic ---
        # Simulate fetching data from a database
        dummy_db_results = self._generate_dummy_results(search_term, num_results)
        # --- END TODO ---

        # Pop the QueryScreen and push the results screen
        self.app.pop_screen()
        self.app.push_screen(QueryResultScreen(dummy_db_results, search_term, page_size=10, verbose=verbose)) # Always use page_size=10 for pagination here

    def _generate_dummy_results(self, search_term: str, count: int) -> list[dict]:
        """Generates dummy results for testing."""
        results = []
        import random
        for i in range(count):
            result = {
                "id": f"DBR{i+1:03d}",
                "name": f"Item {i+1} related to '{search_term}'",
                "type": random.choice(["File", "Function", "Symbol", "Vulnerability"]),
                "path": f"/path/to/some/file_{i}.bin",
                "score": round(random.uniform(0.5, 0.99), 2),
                "details": f"Detailed information for item {i+1}. This could be a very long string that requires scrolling.",
                "tags": random.sample(["tag-a", "tag-b", "tag-c", "tag-d", "tag-e"], random.randint(1, 3))
            }
            results.append(result)
        return results




class MainScreen(Screen):
    """The main screen with file selection and action buttons."""
    selected_path: var[Path | None] = var(None)

    def compose(self) -> ComposeResult:
        yield Header(name="BIDS - Binary Analysis")
        with Container():
            yield DirectoryTree(str("/"), id="tree-view")
            with VerticalScroll(id="actions-pane"):
                yield Static("Selected: None", id="selected-label")
                yield Button("Analyse Selected", id="analyse", disabled=True)
                yield Button("Add to Database", id="add_db", disabled=True)
                yield Button("Query Database", id="query_db")
                yield Button("Generate SBOM", id="generate_sbom", disabled=True)
        yield Footer()

    def watch_selected_path(self, path: Path | None) -> None:
        label = self.query_one("#selected-label", Static)
        can_process = path is not None and (path.is_file() or path.is_dir())
        for button_id in ["#analyse", "#add_db", "#generate_sbom"]:
            self.query_one(button_id, Button).disabled = not can_process
        label.update(f"Selected: {path.name}" if path else "Selected: None")

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        event.stop()
        self.selected_path = event.path

    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        event.stop()
        self.selected_path = event.path

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "generate_sbom" and self.selected_path:
            self.app.push_screen(SbomScreen(target_path=self.selected_path))
        elif event.button.id == "analyse" and self.selected_path:
            self.app.push_screen(AnalyseScreen(target_path=self.selected_path))
        elif event.button.id == "query_db":
            self.app.push_screen(QueryScreen())

class BidsUI(App):
    """A Textual UI for the BIDS ELF analysis tools."""
    CSS_PATH = "bids_style.css"
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "quit", "Quit"),
    ]

    def on_mount(self) -> None:
        self.push_screen(MainScreen())

if __name__ == "__main__":
    app = BidsUI()
    app.run()