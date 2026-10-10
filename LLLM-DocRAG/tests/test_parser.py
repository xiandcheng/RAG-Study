import pytest
from pathlib import Path
from unittest.mock import patch
from app.parser import MarkdownParser
from app.exceptions import DocumentParseError


@pytest.fixture
def parser():
    return MarkdownParser()


# 1. 正常解析 Markdown 文档
def test_parse_success(tmp_path, parser):
    path = tmp_path / "README.md"
    content = """# LoRA
LoRA introduction.

## Parameters
Parameter description.

### Rank
Rank description.
"""
    path.write_text(content, encoding="utf-8")
    metadata = {"owner": "huggingface", "repo": "peft"}

    with patch.object(parser, "_load_metadata", return_value=metadata) as mock_meta:
        result = parser.parse(path)

    assert result.source_path == path
    assert result.title == "LoRA"
    assert result.metadata == metadata
    assert len(result.sections) == 3
    assert [s.title for s in result.sections] == ["LoRA", "Parameters", "Rank"]
    assert [s.level for s in result.sections] == [1, 2, 3]
    mock_meta.assert_called_once_with(path)


# 2. 测试标题回退机制
@pytest.mark.parametrize("content,expected_title", [
    ("# LoRA\nHello", "LoRA"),
    ("## Parameters\nHello", "Parameters"),
    ("### Rank\nHello", "Rank"),
    ("This is normal text.", "README"),
    ("## Parameters\nHello\n# LoRA\nWorld", "LoRA"),
])
def test_parse_title_fallback(tmp_path, parser, content, expected_title):
    path = tmp_path / "README.md"
    path.write_text(content, encoding="utf-8")

    with patch.object(parser, "_load_metadata", return_value={}):
        result = parser.parse(path)

    assert result.title == expected_title


# 3. 测试传入参数类型错误
@pytest.mark.parametrize("path", [
    "README.md",
    None,
    123,
])
def test_parse_invalid_path(parser, path):
    with pytest.raises(TypeError, match="必须是Path类型"):
        parser.parse(path)


# 4. 测试文件不存在
def test_parse_file_not_found(tmp_path, parser):
    path = tmp_path / "not_exist.md"

    with pytest.raises(DocumentParseError, match="Markdown 读取失败"):
        parser.parse(path)


# 5. 测试 Markdown 内容为空
@pytest.mark.parametrize("content", [
    "",
    "   ",
    "\n\n",
    "\t\n  ",
])
def test_parse_empty_content(tmp_path, parser, content):
    path = tmp_path / "empty.md"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(DocumentParseError, match="Markdown 为空"):
        parser.parse(path)


# 6. 测试文件编码错误
def test_parse_invalid_encoding(tmp_path, parser):
    path = tmp_path / "invalid.md"
    path.write_bytes(b"\xff\xfe\xfa")

    with pytest.raises(DocumentParseError, match="Markdown 读取失败"):
        parser.parse(path)


# 7. 测试没有解析出章节
def test_parse_no_sections(tmp_path, parser):
    path = tmp_path / "README.md"
    path.write_text("# LoRA\nHello", encoding="utf-8")

    with patch.object(parser, "_load_metadata", return_value={}), \
         patch.object(parser, "_extract_sections", return_value=[]):
        with pytest.raises(DocumentParseError, match="未解析到有效章节"):
            parser.parse(path)


# 8. 测试元数据读取失败
def test_parse_metadata_error(tmp_path, parser):
    path = tmp_path / "README.md"
    path.write_text("# LoRA\nHello", encoding="utf-8")

    with patch.object(parser, "_load_metadata", side_effect=DocumentParseError("元数据读取失败")):
        with pytest.raises(DocumentParseError, match="元数据读取失败"):
            parser.parse(path)
