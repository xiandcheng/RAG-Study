"""LLM-DocRAG：自动发现并下载 100 篇 Hugging Face 官方 Markdown 文档。

将此文件放在项目根目录（与 run_download.py 同级），运行：
    python run_download_100.py

需要已有 app.downloader.DocumentDownloader 和 app.schemas.DocumentSource。
"""

from __future__ import annotations

import json
import os
from collections import deque
from pathlib import Path
from urllib.parse import quote

import requests

from app.downloader import DocumentDownloader
from app.schemas import DocumentSource
import os

token = os.getenv("GITHUB_TOKEN")

# Transformers 40 / PEFT 25 / TRL 20 / Accelerate 15
TARGETS = [
    ("transformers", "docs/source/en", 40),
    ("peft", "docs/source", 25),
    ("trl", "docs/source", 20),
    ("accelerate", "docs/source", 15),
]
TOTAL = sum(count for _, _, count in TARGETS)
OWNER = "huggingface"

# 优先保留与 LLM/RAG、微调、推理、分布式训练相关的技术文档。
KEYWORD_WEIGHTS = {
    "lora": 14, "quantiz": 12, "quicktour": 11, "quickstart": 11,
    "sft": 13, "dpo": 13, "grpo": 13, "rlhf": 12,
    "trainer": 11, "training": 8, "finetun": 11, "fine_tun": 11,
    "inference": 10, "generation": 10, "chat": 9,
    "pipeline": 9, "model": 5, "tokeniz": 7,
    "fsdp": 12, "deepspeed": 12, "distributed": 11,
    "accelerat": 7, "memory": 8, "peft": 9,
    "dataset": 7, "data": 2, "adapter": 10,
    "installation": 4, "install": 4, "concept": 4,
}


class CachedDocumentDownloader(DocumentDownloader):
    """每个 (owner, repo, ref) 仅解析一次 Commit SHA，避免 100 次 GitHub API 请求。"""

    def __init__(self, save_dir: str | Path, **kwargs):
        super().__init__(save_dir, **kwargs)
        self._commit_cache: dict[tuple[str, str, str], str] = {}

    def _resolve_commit_sha(self, source: DocumentSource) -> str:
        key = (source.owner, source.repo, source.ref)
        if key not in self._commit_cache:
            self._commit_cache[key] = super()._resolve_commit_sha(source)
        return self._commit_cache[key]


def list_markdown_files(session: requests.Session, repo: str, root: str, ref: str, count: int) -> list[dict]:
    """通过 GitHub Contents API 枚举真实存在的文档；不足时逐层深入子目录。"""
    queue = deque([root])
    visited = set()
    files: dict[str, dict] = {}
    max_directories = 14  # 避免消耗过多 GitHub API 配额

    while queue and len(visited) < max_directories:
        folder = queue.popleft()
        if folder in visited:
            continue
        visited.add(folder)
        url = f"https://api.github.com/repos/{OWNER}/{repo}/contents/{quote(folder, safe='/')}"
        response = session.get(url, params={"ref": ref}, timeout=25)
        response.raise_for_status()
        entries = response.json()
        if not isinstance(entries, list):
            raise RuntimeError(f"预期目录但 API 返回其他结构: {repo}/{folder}")

        dirs = []
        for item in entries:
            item_path = item.get("path", "")
            if item.get("type") == "file" and item_path.lower().endswith(".md"):
                if item.get("size", 0) > 0:
                    files[item_path] = {"path": item_path, "size": item.get("size", 0)}
            elif item.get("type") == "dir":
                dirs.append(item_path)

        # 先从重要子目录选文档，再从其他目录补足。
        priority = ("guide", "tutorial", "concept", "package_reference", "reference", "trainer", "how_to", "basic")
        dirs.sort(key=lambda p: (not any(k in p.lower() for k in priority), p))
        queue.extend(dirs)
        if len(files) >= max(count * 3, count + 15):
            break

    return list(files.values())


def quality_score(item: dict) -> tuple:
    path = item["path"].lower()
    stem = Path(path).stem
    score = sum(weight for keyword, weight in KEYWORD_WEIGHTS.items() if keyword in path)
    if stem in {"index", "readme", "contributing", "changelog", "_toctree"}:
        score -= 15
    if "model_doc/" in path:
        score -= 8  # 第一版优先学习性文档，而不是数量庞大的模型 API 模板
    if "package_reference/" in path:
        score -= 3
    if item["size"] < 500:
        score -= 10
    return (-score, path)


def discover_sources(downloader: CachedDocumentDownloader, session: requests.Session) -> tuple[list[DocumentSource], dict[str, str]]:
    chosen: list[DocumentSource] = []
    spare: list[DocumentSource] = []
    pins: dict[str, str] = {}

    for repo, root, count in TARGETS:
        # README.md 仅用于提供合法的 DocumentSource；版本解析本身不读取 path。
        source_for_sha = DocumentSource(owner=OWNER, repo=repo, path="README.md", ref="main")
        commit_sha = downloader._resolve_commit_sha(source_for_sha)
        pins[repo] = commit_sha
        docs = sorted(list_markdown_files(session, repo, root, commit_sha, count), key=quality_score)
        picked = docs[:count]
        print(f"[{repo}] 找到 {len(docs)} 篇 Markdown，选取 {len(picked)} 篇；Commit {commit_sha[:12]}")
        chosen.extend(DocumentSource(owner=OWNER, repo=repo, path=d["path"], ref="main") for d in picked)
        spare.extend(DocumentSource(owner=OWNER, repo=repo, path=d["path"], ref="main") for d in docs[count:])

    # 某个仓库不足配额时，优先从其他仓库的真实文档中补齐。
    if len(chosen) < TOTAL:
        for source in spare:
            if len(chosen) == TOTAL:
                break
            if source not in chosen:
                chosen.append(source)
    if len(chosen) != TOTAL:
        raise RuntimeError(f"只发现 {len(chosen)} 篇文档，未达到 {TOTAL} 篇；请检查 GitHub API 返回和筛选条件")
    return chosen, pins


def main() -> None:
    token = os.getenv("GITHUB_TOKEN")
    session = requests.Session()
    session.headers.update({"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "LLM-DocRAG/1.0"})
    if token:
        session.headers["Authorization"] = f"Bearer {token}"

    downloader = CachedDocumentDownloader(Path("data/raw"), timeout=20, max_retries=2, retry_delay=1.0)
    print("开始获取 GitHub 官方文档清单（四个仓库）……")
    sources, pinned_commits = discover_sources(downloader, session)

    config_path = Path("configs/hf_docs_100.json")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps({
        "selected_count": len(sources), "pinned_commits": pinned_commits,
        "sources": [{"owner": s.owner, "repo": s.repo, "path": s.path, "ref": s.ref} for s in sources],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已保存 100 篇文档清单：{config_path}")

    # 批量下载时会复用缓存 SHA，同一仓库仅进行一次版本解析请求。
    batch = downloader.download_batch(sources)
    print(f"\n下载完成：成功 {len(batch.results)} 篇，失败 {len(batch.errors)} 篇")
    by_status: dict[str, int] = {}
    for result in batch.results:
        by_status[result.status] = by_status.get(result.status, 0) + 1
    print("状态分布：", by_status)
    if batch.errors:
        print("\n失败文档：")
        for key, err in batch.errors.items():
            print(f"  {key}\n    {err}")
        print("\n可以重新运行：已下载且内容未变化的文档会返回 unchanged。")
    print(f"\n输出目录：{downloader.save_dir.resolve()}")


if __name__ == "__main__":
    main()
