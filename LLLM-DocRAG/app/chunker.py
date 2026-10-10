from transformers import AutoTokenizer
from app.schemas import ParsedDocument, DocumentChunk, DocumentSection
import hashlib

class SectionChunker:

    def __init__(self, chunk_size: int = 2048, chunk_overlap: int = 256, tokenizer_name: str = "BAAI/bge-m3"):
        if not 0 <= chunk_overlap < chunk_size:
            raise ValueError("chunk_overlap 必须在 [0, chunk_size) 范围内")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)

    def chunk_document(self, document: ParsedDocument, start_id: int = 1) -> list[DocumentChunk]:
        document_chunks: list[DocumentChunk] = []

        for section_index, section in enumerate(document.sections):
            chunks = self._split_section(section)

            for chunk_index, chunk in enumerate(chunks):
                chunk_id = str(start_id + len(document_chunks))

                document_chunk = DocumentChunk(
                    chunk_id=chunk_id,
                    content=chunk,
                    metadata={
                        **document.metadata,
                        "source_path": document.source_path.as_posix(),
                        "document_title": document.title,
                        "heading_path": section.heading_path,
                        "section_index": section_index,
                        "chunk_index": chunk_index
                    }
                )

                document_chunks.append(document_chunk)

        return document_chunks

    def _split_section(self, section: DocumentSection) -> list[str]:
        if not section.content.strip():
            return []

        token_ids = self.tokenizer.encode(section.content, add_special_tokens=False)
        if len(token_ids) <= self.chunk_size:
            return [section.content]
        step = self.chunk_size - self.chunk_overlap
        chunks = []
        for start in range(0, len(token_ids), step):
            end = min(start + self.chunk_size, len(token_ids))
            chunk_ids = token_ids[start:end]
            chunk_text = self.tokenizer.decode(chunk_ids, skip_special_tokens=False, clean_up_tokenization_spaces=False)

            if chunk_text.strip():
                chunks.append(chunk_text)

            if end == len(token_ids):
                break

        return chunks

    def _count_tokens(self, text: str, add_special_tokens: bool = True) -> int:
        return len(self.tokenizer.encode(text, add_special_tokens=add_special_tokens))
