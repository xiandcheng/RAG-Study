#定义下载器
import math
import time
import hashlib
import os
import urllib
import json
import re
from app.schemas import DocumentSource, DownloaderResult, BatchDownloadResult
from app.exceptions import DownloadError,NetworkError,HTTPStatusError,InvalidDocumentError,StorageError,VersionResolutionError
from pathlib import Path
from urllib.parse import quote
import requests
import logging
import tempfile
from typing import Literal
logger = logging.getLogger(__name__)
DownloadStatus = Literal["downloaded", "updated", "unchanged"]

class DocumentDownloader:

    def __init__(self, save_dir: str | Path, timeout: float = 10.0, max_retries: int = 2, retry_delay: float = 0.5):

        if not isinstance(timeout, (int, float)) or isinstance(timeout, bool):
            raise TypeError("timeout 必须是数字")
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout 必须是大于 0 的有限数")
        if not isinstance(max_retries, int) or isinstance(max_retries, bool):
            raise TypeError("max_retries 必须是整数")
        if max_retries < 0:
            raise ValueError("max_retries 不能小于 0")
        if not isinstance(retry_delay, (int, float)) or isinstance(retry_delay, bool):
            raise TypeError("retry_delay 必须是数字")
        if not math.isfinite(retry_delay) or retry_delay < 0:
            raise ValueError("retry_delay 必须是大于等于 0 的有限数")
        if not isinstance(save_dir, (str, Path)):
            raise TypeError("save_dir 必须是 str 或 Path")
        if not str(save_dir).strip():
            raise ValueError("save_dir 不能为空或全是空格")
        self.save_dir = Path(save_dir)
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def download(self, source: DocumentSource) -> DownloaderResult:
        local_path = self._build_local_path(source)
        commit_sha = self._resolve_commit_sha(source)
        url = self._build_url(source, commit_sha)

        content = self._fetch_with_retry(url)
        content_hash = self._calculate_hash(content)
        content_status = self._determine_status(local_path, content_hash)
        result = DownloaderResult(
            status=content_status,
            file_path=local_path,
            source=source,
            commit_sha=commit_sha,
            content_hash=content_hash
        )
        if content_status != "unchanged":
            self._save_file(content, local_path)
        self._save_metadata(result)
        return result

    def _source_key(self, index : int,source: DocumentSource) -> str:
        return f"{index}:{source.owner}/{source.repo}@{source.ref}:{source.path}"

    def download_batch(self, sources: list[DocumentSource]) -> BatchDownloadResult:
        if not isinstance(sources, list):
            raise TypeError("sources 不是列表")
        if not all(isinstance(source, DocumentSource) for source in sources):
            raise TypeError("sources 列表存在元素不是 DocumentSource")

        batch = BatchDownloadResult()
        for index, source in enumerate(sources):
            try:
                result = self.download(source)
                batch.results.append(result)
            except DownloadError as e:
                batch.errors[self._source_key(index,source)] = str(e)

        return batch

    def _build_metadata_path(self, local_path: Path) -> Path:
        return local_path.with_name(local_path.name + ".meta.json")

    def _save_metadata(self, result: DownloaderResult) -> None:
        data = {
            "schema_version": 1,
            "owner": result.source.owner,
            "repo": result.source.repo,
            "path": result.source.path,
            "ref": result.source.ref,
            "commit_sha": result.commit_sha,
            "content_hash": result.content_hash,
        }
        json_text = json.dumps(data, ensure_ascii=False, indent=2)
        json_bytes = json_text.encode("utf-8")
        self._save_file(json_bytes,self._build_metadata_path(result.file_path))

    def _build_local_path(self, source: DocumentSource) -> Path:
        """
        通过source和save_dir返回真正保存在本地的路径
        :param source: DocumentSource类
        :return: 保存的本地路径
        """
        owner = source.owner
        repo = source.repo
        path = source.path

        if not all(isinstance(s, str) and s.strip() for s in (owner, repo, path)):
            raise InvalidDocumentError("owner、repo、path 不能为空且必须为字符串")

        if any("/" in s or "\\" in s or s in (".", "..") or ":" in s for s in (owner, repo)):
            raise InvalidDocumentError("owner 或 repo 包含非法路径字符")

        if path.startswith(("/", "\\")) or "\\" in path or ":" in path:
            raise InvalidDocumentError("path 不能是绝对路径或包含非法路径字符")

        if any(part in ("", ".", "..") for part in path.split("/")):
            raise InvalidDocumentError("path 包含非法路径段")

        local_path = self.save_dir / owner / repo / path

        if not local_path.resolve().is_relative_to(self.save_dir.resolve()):
            raise InvalidDocumentError("文件路径超出保存目录")

        return local_path

    def _determine_status(self, path: Path, new_hash: str) -> str:
        """
        判断当前下载文件在本地目录的状态
        :param path:
        :param new_hash:
        :return:
        "downloaded"：未下载，可直接下载；
        "updated"：已下载，但需要更新；
        "unchanged"：已下载，不需要更新
        """
        try:
            old_content = path.read_bytes()
        except FileNotFoundError:
            return "downloaded"
        except OSError as e:
            raise StorageError(f"本地读取失败: {path}") from e
        old_hash = self._calculate_hash(old_content)
        if old_hash == new_hash:
            return "unchanged"
        return "updated"

    def _resolve_commit_sha(self, source: DocumentSource) -> str:
        owner = quote(source.owner, safe="")
        repo = quote(source.repo, safe="")
        ref = quote(source.ref, safe="")

        url = f"https://api.github.com/repos/{owner}/{repo}/commits/{ref}"

        try:
            content = self._fetch_with_retry(url)
        except HTTPStatusError as e:
            if e.status_code == 404:
                raise VersionResolutionError("指定版本不存在") from e
            raise
        try:
            data = json.loads(content)
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            raise VersionResolutionError(f"GitHub API 返回非法 JSON: {url}") from e

        if not isinstance(data, dict):
            raise VersionResolutionError(f"GitHub API 响应结构非法: {url}")

        commit_sha = data.get("sha")

        if not isinstance(commit_sha, str) or re.fullmatch(r"[0-9a-fA-F]{40}", commit_sha) is None:
            raise VersionResolutionError(f"GitHub API 返回非法 Commit SHA: {url}")

        return commit_sha.lower()

    def _build_url(self, source: DocumentSource, commit_sha: str) -> str:
        """
        通过source获取下载链接
        :param source: DocumentSource类
        :return: 下载链接
        """
        owner = source.owner.strip("/")
        repo = source.repo.strip("/")
        path = source.path.lstrip("/")
        url = f"https://raw.githubusercontent.com/{quote(owner, safe='')}/{quote(repo, safe='')}/{commit_sha}/{quote(path, safe='/')}"
        return url

    def _fetch(self,url:str)->bytes:
        """
        通过下载链接获取内容
        :param url:
        :return:
        """
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.Timeout as e:
            raise NetworkError(f"请求超时: {url}") from e
        except requests.exceptions.ConnectionError as e:
            raise NetworkError(f"网络连接失败: {url}") from e
        except requests.exceptions.HTTPError as e:
            if e.response is None:
                raise NetworkError(f"HTTP异常缺少响应信息: {url}") from e
            raise HTTPStatusError(e.response.status_code, url) from e
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"HTTP 请求失败: {url}") from e
        if not response.content:
            raise InvalidDocumentError(f"文档内容为空：{url}")
        return response.content

    def _fetch_with_retry(self, url: str) -> bytes:
        """
        下载内容
        :param url:
        :return:
        """
        for attempt in range(self.max_retries + 1):
            try:
                return self._fetch(url)
            except DownloadError as e:
                if not self._should_retry(e) or attempt == self.max_retries:
                    raise
                time.sleep(self.retry_delay*pow(2, attempt))       #采用指数退避法则

    def _should_retry(self, error: DownloadError) -> bool:
        """
        判断哪些需要重试
        :param error:
        :return:
        """
        retryable_status = {429, 500, 502, 503, 504}
        if isinstance(error, HTTPStatusError):
            return error.status_code in retryable_status
        if isinstance(error, NetworkError):
            return True
        return False

    def _calculate_hash(self,content:bytes)->str:
         """
         计算内容哈希值
         :param content: 文档内容
         :return: 文档哈希值
         """
         return hashlib.sha256(content).hexdigest()

    def _save_file(self, content: bytes, path: Path) -> None:
        """
        保存文件
        :param content:
        :param path:
        :return: None
        """
        temp_path: Path | None = None
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent, suffix=".tmp", delete=False) as f:
                temp_path = Path(f.name)
                f.write(content)
            os.replace(temp_path, path)
        except OSError as e:
            raise StorageError(f"文件保存失败: {path}") from e
        finally:
            if temp_path is not None:
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    logger.exception("临时文件清理失败: %s", temp_path)

