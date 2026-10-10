from pathlib import Path
from collections import Counter
from app.parser import MarkdownParser
from app.exceptions import DocumentParseError
import tiktoken
import csv


def main():
    parser = MarkdownParser()
    tokenizer = tiktoken.get_encoding("cl100k_base")
    paths = sorted(Path("data/raw").rglob("*.md"))

    documents = []
    errors = {}
    section_records = []

    # 1. 解析全部 Markdown
    for path in paths:
        try:
            document = parser.parse(path)
            documents.append(document)

            for section in document.sections:
                token_count = len(tokenizer.encode(section.content))
                heading = " > ".join(section.heading_path)
                section_records.append((str(path), heading, token_count))

        except DocumentParseError as e:
            errors[str(path)] = str(e)
            print(f"解析失败: {path}, 原因: {e}")

    if not section_records:
        print("没有可统计的 Section")
        return

    # 2. 统计全部 Section Token
    token_counts = [record[2] for record in section_records]
    total_sections = len(token_counts)
    total_tokens = sum(token_counts)

    print(f"\n文档总数: {len(paths)}")
    print(f"解析成功: {len(documents)}")
    print(f"解析失败: {len(errors)}")
    print(f"Section 总数: {total_sections}")
    print(f"Token 总数: {total_tokens}")

    # 3. 按 Token 长度区间统计
    bins = [(0, 128), (128, 256), (256, 512), (512, 1024), (1024, 2048), (2048, float("inf"))]

    print(f"\n{'Token区间':<18} {'Section数量':<14} {'数量占比':<14} {'Token总量占比'}")
    print("-" * 70)

    for low, high in bins:
        selected = [n for n in token_counts if low <= n < high]
        count = len(selected)
        section_ratio = count / total_sections * 100
        token_ratio = sum(selected) / total_tokens * 100 if total_tokens else 0
        label = f"{low}+" if high == float("inf") else f"{low}-{int(high)}"

        print(f"{label:<18} {count:<14} {section_ratio:<13.2f}% {token_ratio:.2f}%")

    # 4. 统计最常出现的精确 Token 长度
    print("\n出现频率最高的 10 种 Token 长度:")

    for token_count, count in Counter(token_counts).most_common(10):
        print(f"{token_count} Tokens: {count} 个 Section, 占比 {count / total_sections * 100:.2f}%")

    # 5. 保存全部 Section Token 记录
    output_path = Path("data/analysis/section_tokens.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["document", "heading", "token_count"])
        writer.writerows(section_records)

    print(f"\n统计数据已保存: {output_path}")


if __name__ == "__main__":
    main()
