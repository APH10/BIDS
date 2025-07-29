# Copyright (C) 2025 APH10 Limited
# SPDX-License-Identifier: Apache-2.0

import json
import re
from unittest.mock import patch

import pytest
from textual.widgets import Button, Input, Label, Static

from bids.gui import BidsUI
from bids.ui.results import QueryResultScreen


class TestQueryResulsScreen:

    @pytest.mark.asyncio
    async def test_queryresultscreen_renders_correctly(self):

        async with BidsUI().run_test() as pilot:
            # Show the modal screen directly
            await pilot.app.push_screen(
                QueryResultScreen(results=[], search_term="libc")
            )
            screen = pilot.app.screen

            # Check buttons
            assert screen.query_one("#first_page_button", Button).label == "First"
            assert screen.query_one("#prev_page_button", Button).label == "Previous"
            assert screen.query_one("#next_page_button", Button).label == "Next"
            assert screen.query_one("#last_page_button", Button).label == "Last"
            assert screen.query_one("#go_page_button", Button).label == "Go"

            # Simulate pressing close
            await pilot.press("escape")
            # Verify that screen has changed
            active_screen = pilot.app.screen_stack[-1].screen
            assert not isinstance(active_screen, QueryResultScreen)

    # Helper functions

    def extract_static_text(self, static_widget):
        renderable = static_widget.renderable
        raw = repr(renderable)
        # Strip ANSI if present
        return re.sub(r"\x1b\[[0-9;]*m", "", raw).strip()

    def generate_data(self, number):
        result_data = []
        data = {
            "score": 0.5,
            "content": json.dumps(
                {
                    "metadata": {
                        "binary": {"filename": "file1", "description": "A file"}
                    },
                    "components": {
                        "dynamiclibrary": [{"name": "libc_2.so"}, {"name": "libc_3.so"}]
                    },
                }
            ),
        }
        for n in range(number):
            result_data.append(data)
        return result_data

    @pytest.mark.asyncio
    async def test_queryresultscreen_content(self):

        async with BidsUI().run_test() as pilot:
            # Show the modal screen directly
            await pilot.app.push_screen(
                QueryResultScreen(results=self.generate_data(1), search_term="libc")
            )
            screen = pilot.app.screen
            log_display = screen.query_one("#log_display")
            static_widgets = log_display.query(Static).results()
            extracted_texts = [self.extract_static_text(w) for w in static_widgets]
            assert any("file1" in line for line in extracted_texts)

    @pytest.mark.asyncio
    async def test_queryresultscreen_content_multipage(self):

        with patch.object(BidsUI, "notify") as mock_notify:
            async with BidsUI().run_test() as pilot:
                # Show the modal screen directly
                await pilot.app.push_screen(
                    QueryResultScreen(
                        results=self.generate_data(25), search_term="libc"
                    )
                )
                screen = pilot.app.screen
                assert "of 3" in str(
                    screen.query_one("#total_pages_label", Label).renderable
                )
                # Check on page 1
                assert "1" in str(screen.query_one("#page_input", Input).value)
                # Get buttons
                first_btn = screen.query_one("#first_page_button", Button)
                previous_btn = screen.query_one("#prev_page_button", Button)
                next_btn = screen.query_one("#next_page_button", Button)
                last_btn = screen.query_one("#last_page_button", Button)
                goto_btn = screen.query_one("#go_page_button", Button)
                # Move to next page
                next_btn.focus()
                await pilot.press("enter")
                # Should be on page 2
                assert "2" in str(screen.query_one("#page_input", Input).value)
                # Back to previous page
                previous_btn.focus()
                await pilot.press("enter")
                assert "1" in str(screen.query_one("#page_input", Input).value)
                # Go to last page
                last_btn.focus()
                await pilot.press("enter")
                assert "3" in str(screen.query_one("#page_input", Input).value)
                # Go to first page
                first_btn.focus()
                await pilot.press("enter")
                assert "1" in str(screen.query_one("#page_input", Input).value)
                # Go to page
                page_input = screen.query_one("#page_input")
                page_input.value = "3"
                goto_btn.focus()
                await pilot.press("enter")
                assert "3" in str(screen.query_one("#page_input", Input).value)
                # Attempt to go to invalid page
                page_input.value = "A big number"
                goto_btn.focus()
                await pilot.press("enter")
                assert "A big number" in str(
                    screen.query_one("#page_input", Input).value
                )

            mock_notify.assert_called_once()
            assert "Invalid page number." in mock_notify.call_args[0][0]

    @pytest.mark.asyncio
    async def test_queryresultscreen_verbose_content(self):

        async with BidsUI().run_test() as pilot:
            # Show the modal screen directly
            await pilot.app.push_screen(
                QueryResultScreen(
                    results=self.generate_data(1), search_term="libc", verbose=True
                )
            )
            screen = pilot.app.screen
            log_display = screen.query_one("#log_display")
            static_widgets = log_display.query(Static).results()
            extracted_texts = [self.extract_static_text(w) for w in static_widgets]
            assert any("libc_2.so" in line for line in extracted_texts)

    @pytest.mark.asyncio
    async def test_queryresultscreen_noverbose_content(self):

        async with BidsUI().run_test() as pilot:
            # Show the modal screen directly
            await pilot.app.push_screen(
                QueryResultScreen(
                    results=self.generate_data(1), search_term="libc", verbose=False
                )
            )
            screen = pilot.app.screen
            log_display = screen.query_one("#log_display")
            static_widgets = log_display.query(Static).results()
            extracted_texts = [self.extract_static_text(w) for w in static_widgets]
            assert any("libc_2.so" in line for line in extracted_texts) is False

    @pytest.mark.asyncio
    async def test_search(self):

        with patch.object(BidsUI, "notify") as mock_notify:

            async with BidsUI().run_test() as pilot:
                # Show the modal screen directly
                await pilot.app.push_screen(
                    QueryResultScreen(results=[], search_term="libc")
                )
                screen = pilot.app.screen

                # Check search box is hidden
                search_box = screen.query_one("#search_input", Input)
                assert search_box.styles.display == "none"
                # Simulate initiate search
                await pilot.press("/")
                # Verify that screen has changed
                assert search_box.styles.display != "none"
                # Abandon search
                await pilot.press("escape")
                # Check search box hidden again
                assert search_box.styles.display == "none"

            expected_messages = [
                "Enter search term and press Enter. Press Escape to cancel.",
                "Search cleared.",
            ]
            for expected in expected_messages:
                assert any(
                    expected in call.args[0] for call in mock_notify.call_args_list
                )

    @pytest.mark.asyncio
    async def test_search_nomatch_string(self):

        with patch.object(BidsUI, "notify") as mock_notify:

            async with BidsUI().run_test() as pilot:
                # Show the modal screen directly
                await pilot.app.push_screen(
                    QueryResultScreen(results=self.generate_data(1), search_term="libc")
                )
                screen = pilot.app.screen
                search_box = screen.query_one("#search_input", Input)
                # Simulate initiate search
                await pilot.press("/")
                search_box.value = "libc"
                search_box.focus()
                await pilot.press("enter")
                # Try and go to first match
                await pilot.press("n")

            # Check notify was called
            mock_notify.assert_called()
            expected_messages = [
                "Enter search term and press Enter. Press Escape to cancel.",
                "No active search or no matches found.",
            ]
            for expected in expected_messages:
                assert any(
                    expected in call.args[0] for call in mock_notify.call_args_list
                )

    @pytest.mark.asyncio
    async def test_search_match_string(self):

        with patch.object(BidsUI, "notify") as mock_notify:

            async with BidsUI().run_test() as pilot:
                # Show the modal screen directly
                await pilot.app.push_screen(
                    QueryResultScreen(
                        results=self.generate_data(25), search_term="libc"
                    )
                )
                screen = pilot.app.screen
                search_box = screen.query_one("#search_input", Input)
                # Simulate initiate search
                await pilot.press("/")
                search_box.value = "file"
                search_box.focus()
                await pilot.press("enter")
                # Try and go to first match
                await pilot.press("n")
                # Second match
                await pilot.press("n")
                # Back to first
                await pilot.press("p")

            # Check notify was called
            mock_notify.assert_called()
            expected_messages = [
                "Enter search term and press Enter. Press Escape to cancel.",
                "Match 1 of",
                "Match 2 of ",
            ]
            for expected in expected_messages:
                assert any(
                    expected in call.args[0] for call in mock_notify.call_args_list
                )
