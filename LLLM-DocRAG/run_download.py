from pathlib import Path
from app.downloader import DocumentDownloader
from app.schemas import DocumentSource


def main():
    downloader = DocumentDownloader(
        save_dir=Path("data/raw"),
        timeout=15.0,
        max_retries=2,
        retry_delay=1.0
    )

    sources = [
        DocumentSource(owner="huggingface", repo="peft", path="README.md", ref="main"),
        DocumentSource(owner="huggingface", repo="transformers", path="README.md", ref="main"),
        DocumentSource(owner="huggingface", repo="accelerate", path="README.md", ref="main")
    ]

    print("开始下载 GitHub 文档...")
    batch = downloader.download_batch(sources)

    for result in batch.results:
        print(f"\n状态: {result.status}")
        print(f"路径: {result.file_path}")
        print(f"Commit SHA: {result.commit_sha}")
        print(f"SHA-256: {result.content_hash}")
        print(f"文件大小: {result.file_path.stat().st_size} bytes")

    for source_key, error in batch.errors.items():
        print(f"\n下载失败: {source_key}")
        print(f"错误原因: {error}")

    print(f"\n下载完成: 成功 {len(batch.results)} 篇，失败 {len(batch.errors)} 篇")


if __name__ == "__main__":
    main()
