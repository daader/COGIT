import pytest
from datetime import datetime
from core.session import get_session_start_message, get_session_end_message

def test_session_messages(mocker):
    # Mock datetime to have stable tests
    mock_dt = mocker.patch("core.session.datetime")
    mock_now = mocker.Mock()
    mock_now.strftime.return_value = "2024-01-01 12:00"
    mock_dt.now.return_value = mock_now

    assert get_session_start_message() == "chore: session start – 2024-01-01 12:00"
    assert get_session_end_message() == "chore: session end – 2024-01-01 12:00"
