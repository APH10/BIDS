from pathlib import Path
from unittest.mock import patch

import pytest
from textual.widgets import Button, Input, Label

from bids.gui import BidsUI
from bids.ui.analysis import AnalyseScreen
from bids.ui.display import DisplayScreen


class TestAnalyseScreen:

    @pytest.mark.asyncio
    async def test_analyse_screen_renders_correctly(self, tmp_path):
        target_file = tmp_path / "dummy"
        target_file.write_text("dummy")

        async with BidsUI().run_test() as pilot:
            # Show the modal screen directly
            await pilot.app.push_screen(AnalyseScreen(target_path=target_file))
            screen = pilot.app.screen

            # Check title
            label = screen.query_one(Label)
            assert f"Analyse: {target_file.name}" in label.renderable

            # Check input boxes
            description_box = screen.query_one("#description_input", Input)
            assert description_box.placeholder == "e.g., Audit application"

            library_path_box = screen.query_one("#library_path_input", Input)
            assert (
                library_path_box.placeholder == "e.g., /usr/lib/mylibs,./project_libs"
            )

            input_box = screen.query_one("#output_filename_input", Input)
            assert input_box.placeholder == "Leave empty to display"

            # Check buttons
            generate_btn = screen.query_one("#run_analysis_button", Button)
            cancel_btn = screen.query_one("#cancel_button", Button)
            assert generate_btn.label == "Run Analysis"
            assert cancel_btn.label == "Cancel"

            # Simulate pressing cancel
            # Focus and press the cancel button (simulates user input properly)
            cancel_btn.focus()
            await pilot.press("enter")
            # Verify that screen has changed
            active_screen = pilot.app.screen_stack[-1].screen
            assert not isinstance(active_screen, AnalyseScreen)

    @pytest.mark.asyncio
    async def test_generate_analysis_with_filename(self, app):
        target = Path("/fake/binary")

        # Patch both analsyer and output

        with patch("bids.ui.analysis.BIDSAnalyser") as MockAnalyser, patch(
            "bids.ui.analysis.BIDSOutput"
        ) as MockOutput, patch.object(BidsUI, "notify") as mock_notify:

            app = BidsUI()

            async with app.run_test() as pilot:
                screen = AnalyseScreen(target_path=target)
                await app.push_screen(screen)

                # Enter a filename in the input by setting filename directly
                filename_input = screen.query_one("#output_filename_input", Input)
                filename_input.value = "output.json"
                # Click the Run Analysis button
                generate_btn = screen.query_one("#run_analysis_button", Button)
                # Focus and press the run analysis button (simulates user input properly)
                generate_btn.focus()
                await pilot.press("enter")

            # Check mocked processes called
            MockAnalyser.assert_called_once()
            MockOutput.assert_called_once()

            # Check notify was called
            mock_notify.assert_called_once()
            assert "Analysis report saved to" in mock_notify.call_args[0][0]

    @pytest.mark.asyncio
    async def test_generate_analysis_without_filename(self, app):
        target = Path("/fake/binary")

        # Patch both analsyer and output

        with patch("bids.ui.analysis.BIDSAnalyser") as MockAnalyser, patch(
            "bids.ui.analysis.BIDSOutput"
        ) as MockOutput:

            app = BidsUI()

            async with app.run_test() as pilot:
                screen = AnalyseScreen(target_path=target)
                await app.push_screen(screen)

                # Click the Run Analysis button
                generate_btn = screen.query_one("#run_analysis_button", Button)
                # Focus and press the run analysis button (simulates user input properly)
                generate_btn.focus()
                await pilot.press("enter")
                # Check screen is now DisplayScreen
                active_screen = app.screen_stack[-1]
                assert isinstance(active_screen, DisplayScreen)

            # Check mocked processes called
            MockAnalyser.assert_called_once()
            MockOutput.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_analysis_non_ELF_file(self, app):
        target = Path("/fake/binary")

        # Patch both analyser and output

        with patch("bids.ui.analysis.BIDSAnalyser") as MockAnalyser, patch(
            "bids.ui.analysis.BIDSOutput"
        ) as MockOutput, patch.object(BidsUI, "notify") as mock_notify:

            MockAnalyser.return_value.analyse.side_effect = TypeError("Bad file")
            app = BidsUI()

            async with app.run_test() as pilot:
                screen = AnalyseScreen(target_path=target)
                await app.push_screen(screen)

                # Click the Run Analysis button
                generate_btn = screen.query_one("#run_analysis_button", Button)
                # Focus and press the run analysis button (simulates user input properly)
                generate_btn.focus()
                await pilot.press("enter")

            # Check mocked processes called
            MockAnalyser.assert_called_once()
            # No output generated
            MockOutput.assert_not_called()

            # Check notify was called
            mock_notify.assert_called_once()
            assert "Only ELF files can be analysed." in mock_notify.call_args[0][0]

    @pytest.mark.asyncio
    async def test_generate_analysis_missing_file(self, app):
        target = Path("/fake/binary")

        # Patch both analyser and output

        with patch("bids.ui.analysis.BIDSAnalyser") as MockAnalyser, patch(
            "bids.ui.analysis.BIDSOutput"
        ) as MockOutput, patch.object(BidsUI, "notify") as mock_notify:

            MockAnalyser.return_value.analyse.side_effect = FileNotFoundError("Missing")
            app = BidsUI()

            async with app.run_test() as pilot:
                screen = AnalyseScreen(target_path=target)
                await app.push_screen(screen)

                # Click the Run Analysis button
                generate_btn = screen.query_one("#run_analysis_button", Button)
                # Focus and press the run analysis button (simulates user input properly)
                generate_btn.focus()
                await pilot.press("enter")

            # Check mocked processes called
            MockAnalyser.assert_called_once()
            # No output generated
            MockOutput.assert_not_called()

            # Check notify was called
            mock_notify.assert_called_once()
            assert "not found" in mock_notify.call_args[0][0]

    @pytest.mark.asyncio
    async def test_cancel_button_pops_screen(self):
        app = BidsUI()
        async with app.run_test() as pilot:
            screen = AnalyseScreen(target_path=Path("/fake/binary"))
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
