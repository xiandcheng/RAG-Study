from pathlib import Path
from app.schemas import ParsedDocument,DocumentSection
from app.exceptions import DocumentParseError
from typing import Literal,Any
import json
import re

class MarkdownParser:

    def parse(self, path: Path) -> ParsedDocument:
        """
        统一组织解析流程，返回完整文档对象。
        :param path:
        :return:
        """
        if not isinstance(path, Path):
            raise TypeError("传入的path必须是Path类型")
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            raise DocumentParseError(f"Markdown 读取失败: {path}") from e
        if not content.strip():
            raise DocumentParseError(f"Markdown 为空: {path}")

        metadata = self._load_metadata(path)
        sections = self._extract_sections(content)
        if not sections:
            raise DocumentParseError(f"未解析到有效章节: {path}")
        h1_title = next((section.title for section in sections if section.level == 1 and section.title),None)
        fallback_title = next((section.title for section in sections if section.title.strip()), None)
        return ParsedDocument(
            source_path=path,
            title= h1_title or fallback_title or path.stem,
            sections=sections,
            metadata=metadata
        )

    def _extract_sections(self, content: str) -> list[DocumentSection]:
        sections = []
        heading_stack = []
        current_lines = []
        current_title = None
        current_level = 0
        current_path = []

        in_code_block = False
        fence_char = None
        fence_length = 0

        def flush_section():
            if current_title is not None or any(line.strip() for line in current_lines):
                sections.append(DocumentSection(
                    title=current_title or "",
                    level=current_level,
                    content="\n".join(current_lines).strip("\n"),
                    heading_path=current_path.copy()
                ))

        for line in content.splitlines():
            fence = self._parse_fence(line)

            # 1. 当前在代码块内部
            if in_code_block:
                current_lines.append(line)

                if fence is not None:
                    marker, length, info = fence
                    if marker == fence_char and length >= fence_length and not info:
                        in_code_block = False
                        fence_char = None
                        fence_length = 0
                continue

            # 2. 检测代码块开始
            if fence is not None:
                fence_char, fence_length, _ = fence
                in_code_block = True
                current_lines.append(line)
                continue

            # 3. 检测 Markdown 标题
            heading = self._parse_heading(line)

            if heading is not None:
                flush_section()

                level, title = heading

                while heading_stack and heading_stack[-1][0] >= level:
                    heading_stack.pop()

                heading_stack.append((level, title))

                current_title = title
                current_level = level
                current_path = [item[1] for item in heading_stack]
                current_lines = []
                continue

            # 4. 普通正文
            current_lines.append(line)

        # 5. 保存最后一个章节
        flush_section()

        return sections

    def _load_metadata(self, path: Path) -> dict[str, Any]:
        """
        读取对应的 .meta.json 来源信息。
        :param path:本地文档路径名
        :return:字典信息
        """
        meta_path = path.with_name(path.name + ".meta.json")
        try:
            text = meta_path.read_text(encoding="utf-8")
        except FileNotFoundError as e:
            raise DocumentParseError(f"没有对应元数据文件: {meta_path}") from e
        except PermissionError as e:
            raise DocumentParseError(f"文件无读取权限: {meta_path}") from e
        except IsADirectoryError as e:
            raise DocumentParseError(f"这个路径实际上是一个目录: {meta_path}") from e
        except OSError as e:
            raise DocumentParseError(f"元数据读取失败: {meta_path}") from e
        except UnicodeDecodeError as e:
            raise DocumentParseError(f"元数据编码错误: {meta_path}") from e
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise DocumentParseError(f"JSON 格式不合法: {meta_path}") from e
        if not isinstance(data, dict):
            raise DocumentParseError(f"元数据必须是 JSON 对象: {meta_path}")

        return data

    def _parse_heading(self, line: str) -> tuple[int, str] | None:

        match = re.match(r"^ {0,3}(#{1,6})[ \t]+(.+?)\s*$", line)
        if match is None:
            return None
        level = len(match.group(1))
        title = match.group(2).strip()
        if not title:
            return None
        return level, title

    def _parse_fence(self, line: str) -> tuple[str, int, str] | None:
        match = re.fullmatch(r" {0,3}(`{3,}|~{3,})([^\r\n]*)", line)
        if match is None:
            return None
        fence = match.group(1)
        info = match.group(2).strip()
        marker = fence[0]
        length = len(fence)

        if marker == "`" and "`" in info:
            return None
        return marker, length, info

