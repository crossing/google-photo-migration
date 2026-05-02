from unittest.mock import MagicMock, patch

import pytest

from src.core.rate_limiter import rate_limit_retry


def test_rate_limit_retry_success() -> None:
    mock_func = MagicMock(return_value="success")
    decorated = rate_limit_retry()(mock_func)

    assert decorated() == "success"
    assert mock_func.call_count == 1


def test_rate_limit_retry_backoff() -> None:
    mock_func = MagicMock()
    mock_func.__name__ = "mock_func"
    # Fail twice with rate limit, then succeed
    mock_func.side_effect = [
        Exception("429 Too Many Requests"),
        Exception("rate_limit"),
        "success"
    ]

    with patch('time.sleep') as mock_sleep:
        decorated = rate_limit_retry(max_retries=5, base_delay=1.0)(mock_func)
        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 3
        assert mock_sleep.call_count == 2
        # Check that delays are increasing
        args, _ = mock_sleep.call_args_list[0]
        delay1 = args[0]
        args, _ = mock_sleep.call_args_list[1]
        delay2 = args[0]
        assert delay2 > delay1


def test_rate_limit_other_exception() -> None:
    mock_func = MagicMock(side_effect=ValueError("Some other error"))
    decorated = rate_limit_retry()(mock_func)

    with pytest.raises(ValueError, match="Some other error"):
        decorated()
    assert mock_func.call_count == 1
