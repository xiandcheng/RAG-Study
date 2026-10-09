#定义下载器
import math
from app.schemas import DocumentSource, DownloaderResult, BatchDownloadResult
from app.exceptions import DownloadError,NetworkError,HTTPStatusError,InvalidDocumentError
from pathlib import Path
from urllib.parse import quote
import requests
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

    def download(self,source:DocumentSource)->DownloaderResult:
        pass

    def download_batch(self, sources: list[DocumentSource]) -> BatchDownloadResult:
        pass

    def _build_url(self, source: DocumentSource) -> str:
        owner = source.owner.strip("/")
        repo = source.repo.strip("/")
        ref = source.ref.strip("/")
        path = source.path.lstrip("/")
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/{quote(ref, safe='/')}/{quote(path, safe='/')}"
        return url

    def _fetch(self,url:str)->bytes:
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
        pass

    def _should_retry(self, error: DownloadError) -> bool:
        pass
    def _calculate_hash(self,content:bytes)->str:
        pass
    def _save_file(self,content:bytes,path:Path)->None:
        pass



