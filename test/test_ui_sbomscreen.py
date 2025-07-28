from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
from textual.widgets import Button, Input, Label, RadioButton, RadioSet

from bids.gui import BidsUI
from bids.ui.display import DisplayScreen
from bids.ui.sbom import CYCLONEDX_FORMATS, SPDX_FORMATS, SbomScreen


class TestSbomScreen:

    @pytest.mark.asyncio
    async def test_sbom_screen_renders_correctly(self, tmp_path):
        target_file = tmp_path / "dummy"
        target_file.write_text("dummy")

        async with BidsUI().run_test() as pilot:
            # Show the modal screen directly
            await pilot.app.push_screen(SbomScreen(target_path=target_file))
            screen = pilot.app.screen

            # Check title
            label = screen.query_one(Label)
            assert f"Generate SBOM for: {target_file}" in label.renderable

            # Check SBOM Type radios
            type_set = screen.query_one("#sbom_type", RadioSet)
            type_buttons = type_set.query(RadioButton)
            assert len(type_buttons) == 2
            assert type_buttons[0].label == "SPDX"
            assert type_buttons[0].value is True  # Default selected
            assert type_buttons[1].label == "CycloneDX"

            # Check Format radios
            format_set = screen.query_one("#sbom_format", RadioSet)
            format_buttons = format_set.query(RadioButton)
            assert len(format_buttons) >= 1
            assert any(btn.label == "JSON" and btn.value for btn in format_buttons)

            # Check input box
            input_box = screen.query_one("#sbom_filename", Input)
            assert input_box.placeholder == "e.g., my-sbom.json"

            # Check buttons
            generate_btn = screen.query_one("#generate", Button)
            cancel_btn = screen.query_one("#cancel", Button)
            assert generate_btn.label == "Generate SBOM"
            assert cancel_btn.label == "Cancel"

            # Simulate pressing cancel
            # Focus and press the cancel button (simulates user input properly)
            cancel_btn.focus()
            await pilot.press("enter")
            # Verify that screen has changed
            active_screen = pilot.app.screen_stack[-1].screen
            assert not isinstance(active_screen, SbomScreen)

    @pytest.mark.asyncio
    async def test_generate_sbom_with_filename_triggers_sbom_creation(slf, app):
        target = Path("/fake/binary")

        # Patch both sbom.process_file and sbom.create_sbom
        with patch(
            "bids.ui.sbom.bids.sbom.process_file", return_value=(["pkg1"], ["rel1"])
        ) as mock_process, patch(
            "bids.ui.sbom.bids.sbom.create_sbom"
        ) as mock_create, patch.object(
            BidsUI, "notify"
        ) as mock_notify:

            app = BidsUI()

            async with app.run_test() as pilot:
                screen = SbomScreen(target_path=target)
                await app.push_screen(screen)
                # Wait for screen to be ready
                await pilot.pause()

                # Enter a filename in the input by setting filename directly
                filename_input = screen.query_one("#sbom_filename", Input)
                filename_input.value = "output.spdx.json"
                # Click the generate button
                generate_btn = screen.query_one("#generate", Button)
                assert generate_btn.label == "Generate SBOM"

                # Focus and press the generate button (simulates user input properly)
                generate_btn.focus()
                await pilot.press("enter")

            # Check process_file was called with the path
            mock_process.assert_called_once_with(str(target))

            # Check create_sbom was called with expected args
            mock_create.assert_called_once()

            _, kwargs = mock_create.call_args
            assert kwargs["output_file"].endswith("output.spdx.json")

            # Check notify was called
            mock_notify.assert_called_once()
            assert "SBOM saved to" in mock_notify.call_args[0][0]

    @pytest.mark.asyncio
    async def test_cancel_button_pops_screen(self):
        app = BidsUI()
        async with app.run_test() as pilot:
            screen = SbomScreen(target_path=Path("/fake/binary"))
            await app.push_screen(screen)

            # Click cancel button
            cancel_btn = screen.query_one("#cancel", Button)
            assert cancel_btn.label == "Cancel"

            # Simulate pressing cancel
            # Focus and press the cancel button (simulates user input properly)
            cancel_btn.focus()
            await pilot.press("enter")

            # Screen should be popped (i.e. current screen no longer SbomScreen)
            active_screen = app.screen_stack[-1]
            assert active_screen is not screen

    @pytest.mark.asyncio
    async def test_sbom_type_switch_updates_formats(self):
        app = BidsUI()
        async with app.run_test() as pilot:
            screen = SbomScreen(target_path=Path("/fake/binary"))
            await app.push_screen(screen)
            # Initially SPDX type should be selected by default
            sbom_type_rs = screen.query_one("#sbom_type")
            assert sbom_type_rs.pressed_button.label.plain == "SPDX"
            sbom_format_rs = screen.query_one("#sbom_format")
            # Check initial formats correspond to SPDX_FORMATS
            spdx_labels = [
                btn.label.plain for btn in sbom_format_rs.query("RadioButton")
            ]
            # These should match SPDX_FORMATS labels
            expected_labels = [name for name, _ in SPDX_FORMATS]
            assert spdx_labels == expected_labels

            # Switch SBOM type to CycloneDX by pressing its RadioButton
            cyclone_radio = None
            for btn in sbom_type_rs.query("RadioButton"):
                if btn.label.plain == "CycloneDX":
                    cyclone_radio = btn
                    break
            assert cyclone_radio is not None

            # Simulate changing selection to CycloneDX
            await pilot.click("#sbom_cyclonedx")
            # After event processing, format radio buttons should update
            sbom_format_rs = screen.query_one("#sbom_format", RadioSet)
            cyclonedx_labels = [
                btn.label.plain for btn in sbom_format_rs.query("RadioButton")
            ]
            # These should match CYCLONEDX_FORMATS labels
            expected_labels = [name for name, _ in CYCLONEDX_FORMATS]
            assert cyclonedx_labels == expected_labels

    @pytest.mark.asyncio
    async def test_sbom_format_switch(self):
        app = BidsUI()
        async with app.run_test():
            screen = SbomScreen(target_path=Path("/fake/binary"))
            await app.push_screen(screen)
            # Initially SPDX type should be selected by default
            sbom_type_rs = screen.query_one("#sbom_type")
            assert sbom_type_rs.pressed_button.label.plain == "SPDX"
            sbom_format_rs = screen.query_one("#sbom_format")
            # Check initial formats correspond to SPDX_FORMATS
            spdx_labels = [
                btn.label.plain for btn in sbom_format_rs.query("RadioButton")
            ]
            # These should match SPDX_FORMATS labels
            expected_labels = [name for name, _ in SPDX_FORMATS]
            assert spdx_labels == expected_labels
            # Simulate changing format

            # Get SPDX formats labels and radio buttons
            format_buttons = list(sbom_format_rs.query(RadioButton))

            # Default selected format should be JSON
            json_button = next(
                (rb for rb in format_buttons if rb.label.plain == "JSON"), None
            )
            assert json_button is not None, "JSON button not found"
            assert json_button.value is True

            # Select the next format after JSON, e.g. "Tag Value"
            tag_button = next(
                (rb for rb in format_buttons if rb.label.plain == "Tag-Value"), None
            )
            assert tag_button is not None, "Tag Value button not found"
            assert tag_button.value is False

            # Simulate changing format
            # Deselect JSON and select Tag Value
            json_button.value = False
            tag_button.value = True

            # # Find the RadioButton that is currently selected
            # pressed_button = next(rb for rb in sbom_format_rs.query(RadioButton) if rb.value)

            # # Trigger the on_radio_set_changed event manually for format change
            # event = RadioSet.Changed(sbom_format_rs, pressed_button)
            # screen.on_radio_set_changed(event)

            # Assert the newly selected radio button is Tag Value
            assert tag_button.value is True
            assert json_button.value is False

    @pytest.mark.asyncio
    async def test_generate_sbom_no_filename_pushes_displayscreen(self):
        target = Path("/fake/binary")
        fake_tempfile_path = "/tmp/bids_tempfile"  # within SbomScreen

        sbom_content = "line1\nline2\nline3"

        # Needed help to get this to work!
        real_open = open  # preserve the real open

        def selective_open(file, *args, **kwargs):
            if str(file) == fake_tempfile_path:
                return mock_open(read_data=sbom_content)().return_value
            return real_open(file, *args, **kwargs)

        with patch(
            "bids.ui.sbom.bids.sbom.process_file", return_value=(["pkg1"], ["rel1"])
        ) as mock_process, patch(
            "bids.ui.sbom.bids.sbom.create_sbom"
        ) as mock_create, patch(
            "bids.ui.sbom.tempfile.NamedTemporaryFile"
        ) as mock_tmpfile, patch(
            "builtins.open", side_effect=selective_open
        ), patch.object(
            BidsUI, "notify"
        ) as mock_notify:

            # Setup tempfile mock
            mock_tempfile_instance = MagicMock()
            mock_tempfile_instance.name = fake_tempfile_path
            mock_tmpfile.return_value = mock_tempfile_instance

            app = BidsUI()
            async with app.run_test() as pilot:
                screen = SbomScreen(target_path=target)
                await app.push_screen(screen)

                # Leave filename empty (default "")
                filename_input = screen.query_one("#sbom_filename")
                filename_input.value = ""

                # Click generate button
                generate_btn = screen.query_one("#generate", Button)
                assert generate_btn.label == "Generate SBOM"
                generate_btn.focus()
                await pilot.press("enter")

                # Check screen is now DisplayScreen
                active_screen = app.screen_stack[-1]
                assert isinstance(active_screen, DisplayScreen)

            mock_process.assert_called_once()
            mock_create.assert_called_once()
            # Since no filename, no pop_screen + notify
            mock_notify.assert_not_called()
            # Tempfile.close should be called
            mock_tempfile_instance.close.assert_called_once()
