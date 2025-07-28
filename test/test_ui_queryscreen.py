# Copyright (C) 2025 APH10 Limited
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

import pytest
from textual.widgets import Button, Checkbox, Input, Label

from bids.gui import BidsUI
from bids.ui.query import QueryScreen
from bids.ui.results import QueryResultScreen


class TestQueryScreen:

    @pytest.mark.asyncio
    async def test_query_screen_renders_correctly(self):

        async with BidsUI().run_test() as pilot:
            # Show the modal screen directly
            screen = QueryScreen()
            await pilot.app.push_screen(screen)
            screen = pilot.app.screen

            # Check title
            label = screen.query_one(Label)
            assert "Database Query" in label.renderable

            # Check input boxes
            search_box = screen.query_one("#search_term_input", Input)
            assert search_box.placeholder == "e.g., 'malloc', 'libc'..."

            results_box = screen.query_one("#num_results_input", Input)
            assert results_box.placeholder == "e.g., 50"

            verbose_check = screen.query_one("#verbose_checkbox", Checkbox)
            assert "Verbose Reporting" in str(verbose_check.label)

            # Check Nuttons
            query_btn = screen.query_one("#run_query_button", Button)
            cancel_btn = screen.query_one("#cancel_button", Button)
            assert query_btn.label == "Run Query"
            assert cancel_btn.label == "Cancel"

            # Simulate pressing cancel
            # Focus and press the cancel button (simulates user input properly)
            cancel_btn.focus()
            await pilot.press("enter")
            # Verify that screen has changed
            active_screen = pilot.app.screen_stack[-1].screen
            assert not isinstance(active_screen, QueryScreen)

    @pytest.mark.asyncio
    async def test_missing_search_term(self):

        with patch.object(BidsUI, "notify") as mock_notify:
            app = BidsUI()
            async with app.run_test() as pilot:
                screen = QueryScreen()
                await app.push_screen(screen)

                # Click run query button
                query_btn = screen.query_one("#run_query_button", Button)
                # Focus and press the button (simulates user input properly)
                query_btn.focus()
                await pilot.press("enter")

            # Check notify was called
            mock_notify.assert_called_once()
            assert "Please enter a search term." in mock_notify.call_args[0][0]

    @pytest.mark.asyncio
    async def test_negative_number_of_results(self):

        with patch.object(BidsUI, "notify") as mock_notify:
            app = BidsUI()
            async with app.run_test() as pilot:
                screen = QueryScreen()
                await app.push_screen(screen)

                search_box = screen.query_one("#search_term_input", Input)
                search_box.value = "libc"

                results_box = screen.query_one("#num_results_input", Input)
                results_box.value = "-10"

                # Click run query button
                query_btn = screen.query_one("#run_query_button", Button)
                # Focus and press the button (simulates user input properly)
                query_btn.focus()
                await pilot.press("enter")

            # Check notify was called
            mock_notify.assert_called_once()
            assert "Number of results must be positive." in mock_notify.call_args[0][0]

    @pytest.mark.asyncio
    async def test_invalid_number_of_results(self):

        with patch.object(BidsUI, "notify") as mock_notify:
            app = BidsUI()
            async with app.run_test() as pilot:
                screen = QueryScreen()
                await app.push_screen(screen)

                search_box = screen.query_one("#search_term_input", Input)
                search_box.value = "libc"

                results_box = screen.query_one("#num_results_input", Input)
                results_box.value = "This is an invalid number"

                # Click run query button
                query_btn = screen.query_one("#run_query_button", Button)
                # Focus and press the button (simulates user input properly)
                query_btn.focus()
                await pilot.press("enter")

            # Check notify was called
            mock_notify.assert_called_once()
            assert "Invalid number of results." in mock_notify.call_args[0][0]

    @pytest.mark.asyncio
    async def test_cancel(self):
        app = BidsUI()
        async with app.run_test() as pilot:
            screen = QueryScreen()
            await app.push_screen(screen)

            # Click cancel button
            cancel_btn = screen.query_one("#cancel_button", Button)
            assert cancel_btn.label == "Cancel"

            # Simulate pressing cancel
            # Focus and press the cancel button (simulates user input properly)
            cancel_btn.focus()
            await pilot.press("enter")

            # Screen should be popped (i.e. current screen no longer SbomScreen)
            active_screen = app.screen_stack[-1]
            assert active_screen is not screen

    @pytest.mark.asyncio
    async def test_run_query(self):

        with patch("bids.ui.query.BIDSIndexer") as MockQuery:
            app = BidsUI()
            async with app.run_test() as pilot:
                screen = QueryScreen()
                await app.push_screen(screen)

                search_box = screen.query_one("#search_term_input", Input)
                search_box.value = "libc"

                # Click run query button
                query_btn = screen.query_one("#run_query_button", Button)
                # Focus and press the button (simulates user input properly)
                query_btn.focus()
                await pilot.press("enter")
                # Check screen is now DisplayScreen
                active_screen = app.screen_stack[-1]
                assert isinstance(active_screen, QueryResultScreen)

            MockQuery.assert_called_once()
