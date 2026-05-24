import json
from pathlib import Path

import pandas as pd


INPUT_DIR = Path("data/rag_docs/final")
OUTPUT_DIR = Path("data/export")

DOCUMENTS_OUTPUT_PATH = OUTPUT_DIR / "documents_market_data.csv"
CHUNKS_OUTPUT_PATH = OUTPUT_DIR / "chunks_market_data.csv"


def list_to_str(value):
    """
    리스트 데이터를 CSV에 넣기 좋게 문자열로 변환
    """
    if value is None:
        return ""

    if isinstance(value, list):
        return "|".join(map(str, value))

    return str(value)


def dict_to_json_str(value):
    """
    dict 데이터를 CSV 한 칸에 넣기 위해 JSON 문자열로 변환
    """
    if value is None:
        return ""

    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)

    return str(value)


def split_text_to_chunks(text, chunk_size=800, overlap=100):
    """
    긴 content를 chunk로 나누는 함수.
    현재 문서들은 대부분 짧지만, 팀 형식에 맞추기 위해 chunk 구조로 변환.
    """
    if not text:
        return []

    text = str(text).strip()

    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start = end - overlap

        if start < 0:
            start = 0

        if start >= len(text):
            break

    return chunks


def load_final_docs():
    if not INPUT_DIR.exists():
        raise FileNotFoundError(f"{INPUT_DIR} 폴더가 없습니다.")

    json_files = sorted(INPUT_DIR.glob("*.json"))

    if not json_files:
        raise ValueError(f"{INPUT_DIR} 안에 JSON 문서가 없습니다.")

    docs = []

    for file_path in json_files:
        with open(file_path, "r", encoding="utf-8") as f:
            doc = json.load(f)

        docs.append(doc)

    return docs


def build_documents_rows(docs):
    rows = []

    for doc in docs:
        row = {
            "doc_id": doc.get("doc_id", ""),
            "source": doc.get("source", ""),
            "title": doc.get("title", ""),
            "category": doc.get("category", ""),
            "level": doc.get("level", ""),
            "doc_type": doc.get("doc_type", "concept_doc"),
            "ticker": doc.get("ticker", ""),
            "asset_group": doc.get("asset_group", ""),
            "asset_type": doc.get("asset_type", ""),
            "keywords": list_to_str(doc.get("keywords", [])),
            "related_data": list_to_str(doc.get("related_data", [])),
            "related_portfolio_features": list_to_str(doc.get("related_portfolio_features", [])),
            "related_quiz_tags": list_to_str(doc.get("related_quiz_tags", [])),
            "data_snapshot": dict_to_json_str(doc.get("data_snapshot", {})),
            "safe_response_rule": doc.get("safe_response_rule", ""),
            "updated_at": doc.get("updated_at", ""),
            "content": doc.get("content", ""),
        }

        rows.append(row)

    return rows


def build_chunks_rows(docs):
    rows = []

    for doc in docs:
        doc_id = doc.get("doc_id", "")
        content = doc.get("content", "")

        chunks = split_text_to_chunks(content)

        for idx, chunk_text in enumerate(chunks, start=1):
            chunk_id = f"{doc_id}_chunk_{idx:03d}"

            row = {
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "source": doc.get("source", ""),
                "title": doc.get("title", ""),
                "category": doc.get("category", ""),
                "level": doc.get("level", ""),
                "doc_type": doc.get("doc_type", "concept_doc"),
                "chunk_index": idx,
                "chunk_text": chunk_text,
                "keywords": list_to_str(doc.get("keywords", [])),
                "related_data": list_to_str(doc.get("related_data", [])),
                "related_portfolio_features": list_to_str(doc.get("related_portfolio_features", [])),
                "related_quiz_tags": list_to_str(doc.get("related_quiz_tags", [])),
                "safe_response_rule": doc.get("safe_response_rule", ""),
                "updated_at": doc.get("updated_at", ""),
            }

            rows.append(row)

    return rows


def main():
    docs = load_final_docs()

    documents_rows = build_documents_rows(docs)
    chunks_rows = build_chunks_rows(docs)

    documents_df = pd.DataFrame(documents_rows)
    chunks_df = pd.DataFrame(chunks_rows)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    documents_df.to_csv(
        DOCUMENTS_OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    chunks_df.to_csv(
        CHUNKS_OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    print("CSV export 완료")
    print(f"문서 단위 CSV: {DOCUMENTS_OUTPUT_PATH}")
    print(f"문서 수: {len(documents_df)}")
    print(f"청크 CSV: {CHUNKS_OUTPUT_PATH}")
    print(f"청크 수: {len(chunks_df)}")

    print("\nDocuments 컬럼:")
    print(documents_df.columns.tolist())

    print("\nChunks 컬럼:")
    print(chunks_df.columns.tolist())


if __name__ == "__main__":
    main()