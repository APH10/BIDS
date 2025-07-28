import pytest

from bids.gui import BidsUI


@pytest.fixture
def app():
    ui = BidsUI()
    ui.run = lambda *args, **kwargs: None  # prevent actual terminal run
    return ui
