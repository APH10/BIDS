# Copyright (C) 2025 APH10 Limited
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from unittest.mock import patch

import pytest
from textual.widgets import Button, DirectoryTree, Static

from bids.gui import BidsUI, MainScreen, main
from bids.ui.analysis import AnalyseScreen
from bids.ui.query import QueryScreen
from bids.ui.sbom import SbomScreen


# Define a custom mock event to simulate file selection
class DummyFileSelected:
    def __init__(self, control: DirectoryTree, path: Path):
        self.control = control
        self.path = path
        self._stopped = False

    def stop(self):
        self._stopped = True


class DummyDirectorySelected:
    def __init__(self, control, path):
        self.control = control
        self.path = path
        self._stopped = False

    def stop(self):
        self._stopped = True


class TestMainScreen:

    @pytest.mark.asyncio
    async def test_directory_tree_directory_selection(self, tmp_path):
        test_dir = tmp_path

        async with BidsUI().run_test() as pilot:
            screen = pilot.app.screen
            assert isinstance(screen, MainScreen)

            analyse_btn = screen.query_one("#analyse", Button)
            sbom_btn = screen.query_one("#generate_sbom", Button)
            label = screen.query_one("#selected-label", Static)
            tree = screen.query_one(DirectoryTree)

            assert label.renderable == "Selected: None"

            # Simulate selecting a directory
            dummy_event = DummyDirectorySelected(tree, test_dir)
            screen.on_directory_tree_directory_selected(dummy_event)

            # Buttons should now be enabled
            assert not analyse_btn.disabled
            assert not sbom_btn.disabled
            assert label.renderable == f"Selected: {test_dir.name}"

    @pytest.mark.asyncio
    async def test_directory_tree_selection_enables_buttons(self, tmp_path):
        # Create a dummy file for testing
        test_file = tmp_path / "test.txt"
        test_file.write_text("dummy content")

        async with BidsUI().run_test() as pilot:
            screen = pilot.app.screen
            assert isinstance(screen, MainScreen)

            # Confirm all buttons are present
            analyse_btn = screen.query_one("#analyse", Button)
            sbom_btn = screen.query_one("#generate_sbom", Button)
            query_btn = screen.query_one("#query_db", Button)
            label = screen.query_one("#selected-label", Static)
            tree = screen.query_one(DirectoryTree)

            # Check buttons are initially disabled except query_db
            assert analyse_btn.disabled
            assert sbom_btn.disabled
            assert not query_btn.disabled
            assert label.renderable == "Selected: None"

            # Simulate the DirectoryTree selecting a file
            event = DummyFileSelected(tree, test_file)
            screen.on_directory_tree_file_selected(event)

            # Buttons should now be enabled
            assert not analyse_btn.disabled
            assert not sbom_btn.disabled
            assert label.renderable == f"Selected: {test_file.name}"

    @pytest.mark.asyncio
    async def test_select_file_and_buttons_enable(self):
        async with BidsUI().run_test() as pilot:
            screen = pilot.app.screen
            assert isinstance(screen, MainScreen)

            fake_path = Path(__file__)
            screen.watch_selected_path(fake_path)

            label = screen.query_one("#selected-label", Static)
            # assert f"Selected: {fake_path.name}" in label.renderable.plain
            assert label.renderable == f"Selected: {fake_path.name}"

            analyse = screen.query_one("#analyse", Button)
            sbom = screen.query_one("#generate_sbom", Button)
            assert not analyse.disabled
            assert not sbom.disabled

    @pytest.mark.asyncio
    async def test_press_generate_sbom_pushes_screen(self):
        async with BidsUI().run_test() as pilot:
            screen = pilot.app.screen
            assert isinstance(screen, MainScreen)

            fake_path = Path(__file__)
            screen.selected_path = fake_path
            screen.watch_selected_path(fake_path)

            generate_sbom = screen.query_one("#generate_sbom", Button)
            # Click Generate SBOM
            generate_sbom.focus()
            await pilot.press("enter")

            # Check that the screen stack has the correct screen pushed
            top_screen = pilot.app.screen_stack[-1].screen
            assert isinstance(top_screen, SbomScreen)

    @pytest.mark.asyncio
    async def test_press_analyse_pushes_screen(self):
        async with BidsUI().run_test() as pilot:
            screen = pilot.app.screen
            assert isinstance(screen, MainScreen)

            fake_path = Path(__file__)
            screen.selected_path = fake_path
            screen.watch_selected_path(fake_path)

            analyse_file = screen.query_one("#analyse", Button)
            # Click Analyse SBOM
            analyse_file.focus()
            await pilot.press("enter")

            # Check that the screen stack has the correct screen pushed
            top_screen = pilot.app.screen_stack[-1].screen
            assert isinstance(top_screen, AnalyseScreen)

    @pytest.mark.asyncio
    async def test_press_query_pushes_screen(self):
        async with BidsUI().run_test() as pilot:
            screen = pilot.app.screen
            assert isinstance(screen, MainScreen)

            query_db = screen.query_one("#query_db", Button)
            await pilot.click(query_db)

            # Check that the screen stack has the correct screen pushed
            top_screen = pilot.app.screen_stack[-1].screen
            assert isinstance(top_screen, QueryScreen)

    def test_main_runs_app(self):
        with patch.object(BidsUI, "run") as mock_run:
            main()
            mock_run.assert_called_once()
