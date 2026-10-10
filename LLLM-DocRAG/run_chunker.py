from pathlib import Path
from app.parser import MarkdownParser
from app.chunker import SectionChunker


def main():
    root = Path("data/raw/huggingface")
    paths = sorted(root.rglob("*.md"))

    parser = MarkdownParser()
    chunker = SectionChunker(chunk_size=2048, chunk_overlap=256)

    all_chunks = []
    total_sections = 0

    for path in paths:
        document = parser.parse(path)
        total_sections += len(document.sections)

        chunks = chunker.chunk_document(document, start_id=len(all_chunks) + 1)
        all_chunks.extend(chunks)

    print("========== 基本统计 ==========")
    print("文档总数:", len(paths))
    print("章节总数:", total_sections)
    print("Chunk 总数:", len(all_chunks))

    assert all_chunks, "没有生成任何 Chunk"

    print("\n========== Chunk ID 检查 ==========")
    ids = [chunk.chunk_id for chunk in all_chunks]

    assert ids == [str(i) for i in range(1, len(ids) + 1)]
    print("Chunk ID 连续性: 通过")
    print("第一个 Chunk ID:", ids[0])
    print("最后一个 Chunk ID:", ids[-1])

    print("\n========== Token 长度检查 ==========")
    lengths = [len(chunker.tokenizer.encode(chunk.content, add_special_tokens=False)) for chunk in all_chunks]

    print("最小 Token 数:", min(lengths))
    print("最大 Token 数:", max(lengths))
    print("平均 Token 数:", round(sum(lengths) / len(lengths), 2))
    print("超过 2048 Tokens 的 Chunk:", sum(length > chunker.chunk_size for length in lengths))

    assert all(length <= chunker.chunk_size for length in lengths), "存在超长 Chunk"

    print("\n========== Metadata 检查 ==========")
    required_keys = {"source_path", "document_title", "heading_path", "section_index", "chunk_index"}

    for chunk in all_chunks:
        assert required_keys.issubset(chunk.metadata.keys()), f"Metadata 缺少字段: {chunk.chunk_id}"

    print("Metadata 完整性: 通过")

    print("\n========== Chunk 内容预览 ==========")
    for chunk in all_chunks[:5]:
        print(f"\nChunk ID: {chunk.chunk_id}")
        print("来源:", chunk.metadata["source_path"])
        print("标题路径:", " > ".join(chunk.metadata["heading_path"]))
        print("章节索引:", chunk.metadata["section_index"])
        print("片段索引:", chunk.metadata["chunk_index"])
        print("Token 数:", len(chunker.tokenizer.encode(chunk.content, add_special_tokens=False)))
        print("正文预览:", chunk.content[:200].replace("\n", " "))

    print("\n全部测试通过！")


if __name__ == "__main__":
    main()
