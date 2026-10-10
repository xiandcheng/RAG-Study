import pytest
from unittest.mock import Mock, patch
from app.downloader import DocumentDownloader
from app.schemas import DocumentSource, DownloaderResult
from app.exceptions import DownloadError


# 1. 部分成功、部分失败
def test_download_batch_partial_success(tmp_path):
    downloader = DocumentDownloader(tmp_path)
    sources = [
        DocumentSource("huggingface", "peft", "README.md"),
        DocumentSource("huggingface", "peft", "missing.md"),
        DocumentSource("huggingface", "transformers", "README.md")
    ]

    result1 = Mock(spec=DownloaderResult)
    result3 = Mock(spec=DownloaderResult)

    with patch.object(downloader, "download", side_effect=[result1, DownloadError("下载失败"), result3]) as mock_download, \
         patch.object(downloader, "_source_key", return_value="1:missing.md") as mock_key:

        batch = downloader.download_batch(sources)

    assert batch.results == [result1, result3]
    assert batch.errors == {"1:missing.md": "下载失败"}
    assert mock_download.call_count == 3
    mock_key.assert_called_once_with(1, sources[1])


# 2. 所有文档下载成功
def test_download_batch_all_success(tmp_path):
    downloader = DocumentDownloader(tmp_path)
    sources = [
        DocumentSource("huggingface", "peft", "README.md"),
        DocumentSource("huggingface", "transformers", "README.md")
    ]

    results = [Mock(spec=DownloaderResult), Mock(spec=DownloaderResult)]

    with patch.object(downloader, "download", side_effect=results) as mock_download:
        batch = downloader.download_batch(sources)

    assert batch.results == results
    assert batch.errors == {}
    assert mock_download.call_count == 2


# 3. 全部下载失败
def test_download_batch_all_failed(tmp_path):
    downloader = DocumentDownloader(tmp_path)
    sources = [DocumentSource("huggingface", "peft", "README.md")]

    with patch.object(downloader, "download", side_effect=DownloadError("下载失败")), \
         patch.object(downloader, "_source_key", return_value="0:README.md"):

        batch = downloader.download_batch(sources)

    assert batch.results == []
    assert batch.errors == {"0:README.md": "下载失败"}


# 4. 空列表
def test_download_batch_empty(tmp_path):
    downloader = DocumentDownloader(tmp_path)

    with patch.object(downloader, "download") as mock_download:
        batch = downloader.download_batch([])

    assert batch.results == []
    assert batch.errors == {}
    mock_download.assert_not_called()


# 5. sources 本身不是列表
@pytest.mark.parametrize("sources", [
    None,
    "README.md",
    ("README.md",)
])
def test_download_batch_invalid_container(tmp_path, sources):
    downloader = DocumentDownloader(tmp_path)

    with pytest.raises(TypeError, match="sources 不是列表"):
        downloader.download_batch(sources)


# 6. 列表包含非法元素
def test_download_batch_invalid_element(tmp_path):
    downloader = DocumentDownloader(tmp_path)
    sources = [
        DocumentSource("huggingface", "peft", "README.md"),
        "invalid_source"
    ]

    with pytest.raises(TypeError, match="DocumentSource"):
        downloader.download_batch(sources)
