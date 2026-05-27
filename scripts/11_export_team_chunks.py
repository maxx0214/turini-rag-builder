import json
from pathlib import Path
from datetime import datetime


INPUT_DIR = Path("data/rag_docs/final")
OUTPUT_DIR = Path("data/export")

OUTPUT_JSONL_PATH = OUTPUT_DIR / "chunks_market_data.jsonl"
OUTPUT_JSON_PATH = OUTPUT_DIR / "chunks_market_data.json"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


def normalize_topic(category, doc_type, source):
    """
    팀 공통 topic 필드에 맞추기 위한 간단한 매핑.
    필요하면 팀과 논의해서 topic 이름을 더 통일하면 됨.
    """
    text = f"{category} {doc_type} {source}".lower()

    if "금리" in text or "fedfunds" in text or "dgs10" in text:
        return "interest_rate"

    if "cpi" in text or "물가" in text or "인플레이션" in text:
        return "inflation"

    if "gdp" in text or "경기" in text:
        return "macro_economy"

    if "실업" in text or "unrate" in text:
        return "employment"

    if "etf" in text:
        return "etf"

    if "stock" in text or "주식" in text or "개별주" in text:
        return "stock"

    if "bond" in text or "채권" in text or "treasury" in text:
        return "bond"

    return "market_data"


def normalize_source_name(source):
    if not source:
        return "Turini"

    source = str(source)

    if source.lower() == "fred":
        return "FRED"

    if source.lower() == "yfinance":
        return "yfinance"

    return source


def make_source_url(source, related_data):
    """
    FRED는 대표 URL을 넣고, yfinance는 개별 티커 URL을 특정하기 어려우므로 yfinance 메인으로 처리.
    """
    source = str(source).lower()

    if source == "fred":
        if isinstance(related_data, list) and related_data:
            series_id = str(related_data[0])
            return f"https://fred.stlouisfed.org/series/{series_id}"
        return "https://fred.stlouisfed.org/"

    if source == "yfinance":
        return "https://finance.yahoo.com/"

    return ""


def clean_text(text):
    if text is None:
        return ""

    text = str(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    lines = []
    for line in text.split("\n"):
        line = line.strip()
        if line:
            lines.append(line)

    return "\n".join(lines)


def split_text_to_chunks(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """
    문자 기준 청킹.
    팀 기준:
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 100
    """
    text = clean_text(text)

    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - overlap

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


def build_chunks(docs):
    all_chunks = []

    for doc in docs:
        doc_id = doc.get("doc_id", "").strip()

        if not doc_id:
            doc_id = Path(doc.get("title", "unknown_doc")).stem

        title = doc.get("title", "")
        content = doc.get("content", "")
        source = doc.get("source", "")
        category = doc.get("category", "")
        doc_type = doc.get("doc_type", "")
        related_data = doc.get("related_data", [])

        source_name = normalize_source_name(source)
        source_url = doc.get("source_url") or make_source_url(source, related_data)
        topic = doc.get("topic") or normalize_topic(category, doc_type, source)
        published_date = doc.get("published_date") or doc.get("updated_at") or datetime.today().strftime("%Y-%m-%d")

        text_chunks = split_text_to_chunks(content)

        total_chunks = len(text_chunks)

        for idx, text in enumerate(text_chunks):
            chunk_id = f"{doc_id}_c{idx:03d}"

            prev_chunk_id = None
            next_chunk_id = None

            if idx > 0:
                prev_chunk_id = f"{doc_id}_c{idx - 1:03d}"

            if idx < total_chunks - 1:
                next_chunk_id = f"{doc_id}_c{idx + 1:03d}"

            embedding_text = f"{title}\n\n{text}".strip()

            row = {
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "chunk_index": idx,
                "total_chunks": total_chunks,
                "prev_chunk_id": prev_chunk_id,
                "next_chunk_id": next_chunk_id,
                "source_name": source_name,
                "source_url": source_url,
                "title": title,
                "topic": topic,
                "published_date": published_date,
                "text": text,
                "embedding_text": embedding_text,
                "char_count": len(text),
            }

            all_chunks.append(row)

    return all_chunks


def save_jsonl(chunks):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_JSONL_PATH, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")


def save_json(chunks):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)


def main():
    docs = load_final_docs()
    chunks = build_chunks(docs)

    save_jsonl(chunks)
    save_json(chunks)

    print("팀 형식 청크 export 완료")
    print(f"입력 문서 수: {len(docs)}")
    print(f"생성 청크 수: {len(chunks)}")
    print(f"JSONL 저장 위치: {OUTPUT_JSONL_PATH}")
    print(f"JSON 저장 위치: {OUTPUT_JSON_PATH}")

    if chunks:
        print("\n첫 번째 청크 예시:")
        print(json.dumps(chunks[0], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()