from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Static
from textual.containers import Container, VerticalScroll
from textual import on
from textual.binding import Binding
from textual.message import Message
from textual.widget import Widget
from textual.reactive import reactive, Reactive
from rich.text import Text
from textual.events import Key

# Custom Highlighter
class SearchHighlighter:
    def __init__(self, search_term: str = "", current_match_line: int | None = None) -> None:
        super().__init__()
        self.search_term = search_term.lower()
        self.current_match_line = current_match_line # New: The line number of the currently selected match

    def __call__(self, text: Text, line_number: int) -> Text: # New: Accept line_number
        """Applies highlighting to the given Text object."""
        if not self.search_term:
            return text

        plain_text = text.plain.lower()
        start = 0
        while True:
            idx = plain_text.find(self.search_term, start)
            if idx == -1:
                break
            end = idx + len(self.search_term)

            if line_number == self.current_match_line:
                # Highlight the current match with a distinct style (e.g., bold green on red)
                text.stylize("b green on red", idx, end)
            else:
                # Highlight other matches with the regular style (e.g., bold black on yellow)
                text.stylize("b black on yellow", idx, end)
            start = end
        return text

# A custom widget to contain and manage log lines
class LogContainer(Container):
    search_term: Reactive[str] = reactive("", always_update=True)
    current_match_line: Reactive[int | None] = reactive(None) # New: Pass down current_match_line

    def __init__(self, *children: Widget, name: str | None = None, id: str | None = None, classes: str | None = None, disabled: bool = False) -> None:
        super().__init__(*children, name=name, id=id, classes=classes, disabled=disabled)
        self._current_highlighter = SearchHighlighter("", None) # Update highlighter init

    def watch_search_term(self, new_search_term: str) -> None:
        # Re-initialize highlighter to update its internal search_term
        self._current_highlighter = SearchHighlighter(new_search_term, self.current_match_line)

    def watch_current_match_line(self, new_line: int | None) -> None:
        # Re-initialize highlighter to update its internal current_match_line
        self._current_highlighter = SearchHighlighter(self.search_term, new_line)

    def render_log_lines(self, all_messages: list[str]) -> None:
        """Renders all log messages as Static widgets with the current highlighter."""
        self.remove_children() # Clear existing log lines
        for i, msg in enumerate(all_messages): # New: Enumerate to get line number
            rich_text = Text(msg)
            highlighted_text = self._current_highlighter(rich_text, i) # Pass line number
            self.mount(Static(highlighted_text))

# Custom Input widget to handle the Escape key
class SearchInput(Input):
    """An Input widget for search with custom key handling."""
    def on_key(self, event: Key) -> None:
        """Handles specific key presses like 'escape'."""
        if event.key == "escape":
            self.app.post_message(SearchCleared())
            self.value = ""
            event.stop() # Stop the event from propagating further
            return

class SearchCleared(Message):
    """Posted when the search is cleared."""
    pass

class MyApp(App):
    BINDINGS = [
        Binding("slash", "toggle_search", "Search", show=True, key_display="/"),
        Binding("n", "next_match", "Next Match", show=False), # New binding for next match
        Binding("p", "previous_match", "Previous Match", show=False), # New binding for previous match
    ]

    _all_log_messages: list[str] = [] # Stores raw log strings
    _match_indices: list[int] = [] # Stores line numbers (indices in _all_log_messages) of all matches
    current_match_index: Reactive[int | None] = reactive(None) # Index within _match_indices list

    # Reactive property to control search input visibility
    show_search_input: Reactive[bool] = reactive(False)

    # CSS block
    CSS = """
    Screen {
        layout: vertical; /* Ensure the top-level screen container uses vertical layout */
    }
    Header {
        height: auto;
    }
    Footer {
        height: auto;
    }

    Container { /* This refers to the main content container in compose */
        layout: vertical; /* Crucial: make the main content container use vertical layout */
        height: 1fr; /* Make this container fill available vertical space */
    }

    #log_display_container {
        height: 1fr; /* Log scroll view takes all available fractional height */
    }
    #log_display {
        /* Ensure the LogContainer itself allows its content to dictate its height */
        height: auto;
        width: 100%; /* Ensure it fills the scroll view horizontally */
    }

    #search_input {
        height: auto; /* Allow input to size naturally */
        margin-top: 1; /* Add a little space above it */
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        # The main content container will manage the layout of log and search
        with Container():
            # VerticalScroll for the log data, takes remaining space
            with VerticalScroll(id="log_display_container", classes="log-scroll-view"):
                yield LogContainer(id="log_display")
            # Input box will be pushed to the bottom
            yield Input(placeholder="Search...", id="search_input")
        yield Footer()

    # Watcher for show_search_input reactive property
    def watch_show_search_input(self, show_input: bool) -> None:
        """Called when the show_search_input reactive property changes."""
        search_input = self.query_one("#search_input", Input)
        if show_input:
            search_input.styles.display = "block" # Make it visible
            search_input.focus()
            self.notify("Enter search term and press Enter. Press Escape to cancel.", timeout=3)
        else:
            search_input.styles.display = "none" # Make it hidden
            search_input.blur()

    # New: Watcher for current_match_index to update LogContainer and scroll
    def watch_current_match_index(self, new_index: int | None) -> None:
        log_container = self.query_one("#log_display", LogContainer)
        if new_index is not None and self._match_indices:
            line_to_highlight = self._match_indices[new_index]
            log_container.current_match_line = line_to_highlight # Update LogContainer's reactive
            self._redraw_log_content(log_container.search_term) # Re-render to show new highlight
            
            # Scroll to the highlighted line
            # The Static widgets are children of LogContainer, which is in VerticalScroll
            scroll_view = self.query_one("#log_display_container", VerticalScroll)
            log_content_widgets = log_container.children # These are the Static widgets

            if 0 <= line_to_highlight < len(log_content_widgets):
                scroll_view.scroll_to_widget(
                    log_content_widgets[line_to_highlight], top=True, animate=True
                )
            self.notify(f"Match {new_index + 1} of {len(self._match_indices)}", timeout=1)
        else:
            # If no matches or current_match_index is None, clear current highlight
            log_container.current_match_line = None
            self._redraw_log_content(log_container.search_term) # Re-render to remove specific highlight
            # No specific scroll if no highlight

    def on_mount(self) -> None:
        """Populates initial log messages and sets up the display."""
        # Populate _all_log_messages with initial data
        for i in range(200): # 200 lines for testing scrolling
            message = f"Log message {i}: This is some important information. This is a very long line to test wrapping and scrolling functionality. It should ideally wrap within the container. "
            if i % 3 == 0:
                message = f"ERROR: An error occurred at line {i/3}. Critical error message that spans multiple words."
            if i % 5 == 0:
                message = f"WARNING: Watch out for event {i/5}. Potential issue identified with the system component."
            self._all_log_messages.append(message)

        # Initial redraw of the log content to populate the display
        self._redraw_log_content("")

        # Ensure search input is hidden initially by setting the reactive
        self.show_search_input = False


    def action_toggle_search(self) -> None:
        """Toggles the visibility of the search input."""
        # Toggle the reactive property, which will trigger the watcher
        self.show_search_input = not self.show_search_input
        
        # When opening, clear the input value
        if self.show_search_input:
            self.query_one("#search_input", Input).value = ""


    @on(Input.Submitted, "#search_input")
    def apply_search_and_highlight(self, event: Input.Submitted) -> None:
        """Applies the search term and refreshes the log display."""
        search_term = event.value.strip()
        log_container = self.query_one("#log_display", LogContainer)

        log_container.search_term = search_term

        # Find all matches and store their line numbers
        self._match_indices = []
        if search_term: # Only search if term is not empty
            for i, msg in enumerate(self._all_log_messages):
                if search_term.lower() in msg.lower():
                    self._match_indices.append(i)

        # Initialize current_match_index, which will trigger its watcher
        if self._match_indices:
            self.current_match_index = 0 # Go to the first match
        else:
            self.current_match_index = None # No matches, clear current highlight
        
        # Hide search input
        self.show_search_input = False

    @on(SearchCleared)
    def handle_search_cleared(self) -> None:
        """Handles the SearchCleared message to reset the display."""
        log_container = self.query_one("#log_display", LogContainer)
        log_container.search_term = ""
        
        self.current_match_index = None # Reset current match
        self._match_indices = [] # Clear all matches

        self.show_search_input = False
        self.notify("Search cleared.", timeout=1)
        self._redraw_log_content("") # Force full redraw to remove all highlights

    # New: Action to move to the next match
    def action_next_match(self) -> None:
        if self._match_indices:
            if self.current_match_index is None:
                self.current_match_index = 0 # If no match selected, go to first
            else:
                self.current_match_index = (self.current_match_index + 1) % len(self._match_indices)
        else:
            self.notify("No active search or no matches found.", timeout=1)

    # New: Action to move to the previous match
    def action_previous_match(self) -> None:
        if self._match_indices:
            if self.current_match_index is None:
                self.current_match_index = len(self._match_indices) - 1 # If no match selected, go to last
            else:
                self.current_match_index = (self.current_match_index - 1 + len(self._match_indices)) % len(self._match_indices)
        else:
            self.notify("No active search or no matches found.", timeout=1)

    def _redraw_log_content(self, current_search_term: str) -> None:
        """Helper method to clear and redraw the log content with current highlighting."""
        log_container = self.query_one("#log_display", LogContainer)
        
        # Pass the current match line to the LogContainer so it can update its highlighter
        log_container.current_match_line = (
            self._match_indices[self.current_match_index]
            if self.current_match_index is not None and self._match_indices
            else None
        )
        
        log_container.render_log_lines(self._all_log_messages)

        # If a match is selected, scrolling is handled by watch_current_match_index.
        # Otherwise, if search is cleared or no matches, scroll to end.
        if self.current_match_index is None:
            self.query_one("#log_display_container", VerticalScroll).scroll_end()

        # Removed redundant notification here, as watch_current_match_index and Input.Submitted handle it
        # You can add back a general "no matches found" here if desired for non-search-submission scenarios
        # if current_search_term and not self._match_indices:
        #     self.notify(f"No matches found for '{current_search_term}'.", timeout=3)


if __name__ == "__main__":
    app = MyApp()
    app.run()