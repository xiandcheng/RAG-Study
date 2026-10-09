#定义异常体系
class DownloadError(Exception):
    """
    作为所有下载异常的基类
    """
    pass

class NetworkError(DownloadError):
    """
    保存网络错误信息
    """
    pass

class HTTPStatusError(DownloadError):
    """
    保存 HTTP 状态码和 URL
    """
    def __init__(self, status_code:int,url:str):
        self.status_code = status_code
        self.url = url
        message = f"HTTP请求失败: status_code={status_code}, url={url}"
        super().__init__(message)


class InvalidDocumentError(DownloadError):
    """
    表示文档内容不合法
    """
    pass

class StorageError(DownloadError):
    """
    表示文件存储失败
    """
    pass

class VersionResolutionError(DownloadError):
    """
    表示无法解析 GitHub 版本
    """
    pass

