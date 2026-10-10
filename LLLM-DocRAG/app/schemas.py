#定义数据结构
from dataclasses import dataclass, field
from typing import Literal,Any
from pathlib import Path


@dataclass
class DocumentSource:
    owner:str
    repo:str
    path:str    #分支名
    ref:str = 'main'

# source = DocumentSource(
#     owner="huggingface",
#     repo="peft",
#     path="docs/source/package_reference/lora.md",
#     ref="main"
# )

@dataclass
class DownloaderResult:
    status: Literal["downloaded", "updated", "unchanged"]              #downloaded：文件首次下载成功；updated：远程内容变化，本地文件已更新；unchanged：内容未变化，无需更新
    file_path:Path
    source:DocumentSource
    commit_sha:str          #版本号
    content_hash:str        #文档哈希值
    def __post_init__(self):
        """
        处理status非法值
        :return: 向上抛出异常
        """
        valid_status = ("downloaded", "updated", "unchanged")
        if self.status not in valid_status:
            raise ValueError(f"无效的下载状态: {self.status}")

@dataclass
class BatchDownloadResult:
    results: list[DownloaderResult] = field(default_factory=list)
    errors: dict[str, str] = field(default_factory=dict)

@dataclass
class DocumentSection:
    title: str
    level: int
    content: str
    heading_path: list[str]

@dataclass
class ParsedDocument:
    source_path: Path
    title: str
    sections: list[DocumentSection] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class DocumentChunk:
    chunk_id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

