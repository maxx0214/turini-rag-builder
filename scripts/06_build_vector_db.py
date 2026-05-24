import json
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


DOCS_DIR = Path("data/rag_docs/final")
VECTOR_DB_PATH = "data/vector_db"
COLLECTION_NAME = "turini_education_docs"


def load_docs():
    if not DOCS_DIR.exists():
        raise FileNotFoundError(f"{DOCS_DIR} 폴더가 없습니다.")

    docs = []

    for file_path in DOCS_DIR.glob("*.json"):
        with open(file_path, "r", encoding="utf-8") as f:
            doc = json.load(f)

        docs.append(doc)

    if not docs:
        raise ValueError(f"{DOCS_DIR} 안에 JSON 문서가 없습니다.")

    return docs


def build_embedding_text(doc):
    title = doc.get("title", "")
    category = doc.get("category", "")
    keywords = ", ".join(doc.get("keywords", []))
    related_quiz_tags = ", ".join(doc.get("related_quiz_tags", []))
    related_portfolio_features = ", ".join(doc.get("related_portfolio_features", []))
    content = doc.get("content", "")

    return f"""
제목: {title}
카테고리: {category}
키워드: {keywords}
관련 퀴즈 태그: {related_quiz_tags}
관련 포트폴리오 특징: {related_portfolio_features}

본문:
{content}
""".strip()


def main():
    docs = load_docs()

    print(f"문서 로드 완료: {len(docs)}개")

    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)

    # 기존 collection이 있으면 삭제 후 새로 생성
    try:
        client.delete_collection(name=COLLECTION_NAME)
        print(f"기존 collection 삭제 완료: {COLLECTION_NAME}")
    except Exception:
        pass

    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    print("임베딩 모델 로드 중...")
    model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

    ids = []
    embeddings = []
    documents = []
    metadatas = []

    for doc in docs:
        doc_id = doc["doc_id"]
        embedding_text = build_embedding_text(doc)
        embedding = model.encode(embedding_text).tolist()

        ids.append(doc_id)
        embeddings.append(embedding)
        documents.append(doc["content"])
        metadatas.append({
            "title": doc.get("title", ""),
            "category": doc.get("category", ""),
            "level": doc.get("level", 1),
            "source": doc.get("source", ""),
            "updated_at": doc.get("updated_at", ""),
        })

        print(f"임베딩 완료: {doc_id} / {doc.get('title', '')}")

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )

    print("\nVector DB 저장 완료")
    print(f"저장 위치: {VECTOR_DB_PATH}")
    print(f"Collection 이름: {COLLECTION_NAME}")
    print(f"저장 문서 수: {len(ids)}개")


if __name__ == "__main__":
    main()