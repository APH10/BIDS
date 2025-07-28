import pytest
from textual.widgets import Button

from bids.gui import BidsUI
from bids.ui.display import DisplayScreen


class TestDisplayScreen:

    @pytest.mark.asyncio
    async def test_displayscreen_renders_correctly(self):

        async with BidsUI().run_test() as pilot:
            # Show the modal screen directly
            await pilot.app.push_screen(
                DisplayScreen(content=["This is a line"], content_type="Test Data")
            )
            screen = pilot.app.screen

            # Check buttons
            close_btn = screen.query_one("#close_button", Button)
            assert close_btn.label == "Close"

            # Simulate pressing close
            # Focus and press the cancel button (simulates user input properly)
            close_btn.focus()
            await pilot.press("enter")
            # Verify that screen has changed
            active_screen = pilot.app.screen_stack[-1].screen
            assert not isinstance(active_screen, DisplayScreen)
