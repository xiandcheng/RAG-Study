
import pytest
from pathlib import Path
from app.downloader import DocumentDownloader


@pytest.mark.parametrize("timeout", [-1, 0, float("inf"), float("nan")])
def test_invalid_timeout(timeout):
    with pytest.raises(ValueError):
        DocumentDownloader(save_dir=Path("./downloads"), timeout=timeout)


@pytest.mark.parametrize("max_retries", [-1, -5])
def test_invalid_max_retries(max_retries):
    with pytest.raises(ValueError):
        DocumentDownloader(save_dir=Path("./downloads"), max_retries=max_retries)
@pytest.mark.parametrize("retry_delay", [
    -1,
    float("inf"),
    float("-inf"),
    float("nan")
])
def test_invalid_retry_delay(retry_delay):
    with pytest.raises(ValueError):
        DocumentDownloader(save_dir=Path("./downloads"), retry_delay=retry_delay)
def test_zero_retry_delay():
    downloader = DocumentDownloader(save_dir="./downloads", retry_delay=0)
    assert downloader.retry_delay == 0
from unittest.mock import Mock, patch
from app.downloader import DocumentDownloader


def test_fetch_success():
    downloader = DocumentDownloader(save_dir="./downloads")

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = b"Hello RAG"
    mock_response.raise_for_status.return_value = None

    with patch("app.downloader.requests.get", return_value=mock_response):
        result = downloader._fetch("https://example.com/test.md")

    assert result == b"Hello RAG"
