import pytest

from anomaly_analyzer.state import AppState


@pytest.fixture
def test_state():
    return AppState()


def test_update_parameters(test_state):
    form_data = {
        "tickers": "11110, 22220",
        "anomaly_type": "month_end",
        "slippage": "0.2",
    }

    test_state.update_parameters(form_data)

    assert test_state.target_tickers_input == "11110, 22220"
    assert test_state.target_tickers == ["11110", "22220"]
    assert test_state.target_anomaly == "month_end"
    assert test_state.slippage_pct == 0.2


def test_clear_error(test_state):
    test_state.error_message = "Some error"
    test_state.clear_error()
    assert test_state.error_message == ""


def test_set_phase(test_state):
    test_state._set_phase("fetching", "Getting data...")
    assert test_state.loading_phase.phase == "fetching"
    assert test_state.loading_phase.message == "Getting data..."
