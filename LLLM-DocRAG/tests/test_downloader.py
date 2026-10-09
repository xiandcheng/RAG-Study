import pytest
from pathlib import Path
from unittest.mock import patch, call

from app import downloader
from app.downloader import DocumentDownloader
from app.exceptions import HTTPStatusError


def test_retry_exponential_backoff():
    downloader = DocumentDownloader(Path("./data/raw"), max_retries=2, retry_delay=0.5)
    url = "https://example.com/test.md"

    # 模拟两次 HTTP 503，第三次成功
    responses = [
        HTTPStatusError(503, url),
        HTTPStatusError(503, url),
        b"hello"
    ]

    # 同时模拟网络请求和 sleep
    with patch.object(downloader, "_fetch", side_effect=responses) as mock_fetch, patch("app.downloader.time.sleep") as mock_sleep:
        result = downloader._fetch_with_retry(url)

    # 检查最终返回值
    assert result == b"hello"

    # 检查请求次数
    assert mock_fetch.call_count == 3

    # 检查等待次数及每次的等待时间
    assert mock_sleep.call_count == 2
    assert mock_sleep.call_args_list == [call(0.5), call(1.0)]



def test_no_retry_on_404():

    downloader = DocumentDownloader(Path("./data/raw"), max_retries=2, retry_delay=0.5)
    url = "https://example.com/test.md"
    responses = [
            HTTPStatusError(404, url)
        ]
    with patch.object(downloader, "_fetch", side_effect=responses) as mock_fetch, patch("app.downloader.time.sleep") as mock_sleep:
        with pytest.raises(HTTPStatusError):
            downloader._fetch_with_retry(url)
    assert mock_fetch.call_count == 1
    assert mock_sleep.call_count == 0


def test_retry_exhausted():
    downloader = DocumentDownloader(Path("./data/raw"), max_retries=2, retry_delay=0.5)
    url = "https://example.com/test.md"

    responses = [
        HTTPStatusError(503, url),
        HTTPStatusError(503, url),
        HTTPStatusError(503, url)
    ]

    with patch.object(downloader, "_fetch", side_effect=responses) as mock_fetch, patch("app.downloader.time.sleep") as mock_sleep:
        with pytest.raises(HTTPStatusError):
            downloader._fetch_with_retry(url)

    assert mock_fetch.call_count == 3
    assert mock_sleep.call_count == 2
def test_same_hash():
    downloader = DocumentDownloader(Path("./data/raw"))
    content = b"hello"

    result1 = downloader._calculate_hash(content)
    result2 = downloader._calculate_hash(content)

    assert result1 == result2

def test_different_hash():
    downloader = DocumentDownloader(Path("./data/raw"))
    content1 = b"hello"
    content2 = b"world"
    result1 = downloader._calculate_hash(content1)
    result2 = downloader._calculate_hash(content2)

    assert result1 != result2

def test_save_file_success(tmp_path):
    downloader = DocumentDownloader(tmp_path)
    path = tmp_path / "docs" / "test.md"
    content = b"Hello RAG"

    downloader._save_file(content, path)

    assert path.exists()
    assert path.read_bytes() == content
