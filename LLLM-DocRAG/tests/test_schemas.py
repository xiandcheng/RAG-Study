import pytest
from pathlib import Path
from app.schemas import DocumentSource, DownloaderResult


def test_valid_status():
    source = DocumentSource(owner="huggingface", repo="peft", path="README.md")

    result = DownloaderResult(
        status="downloaded",
        file_path=Path("README.md"),
        source=source,
        commit_sha="abc123",
        content_hash="hash123"
    )

    assert result.status == "downloaded"


def test_invalid_status():
    source = DocumentSource(owner="huggingface", repo="peft", path="README.md")

    with pytest.raises(ValueError, match="无效的下载状态"):
        DownloaderResult(
            status="failed",
            file_path=Path("README.md"),
            source=source,
            commit_sha="abc123",
            content_hash="hash123"
        )
