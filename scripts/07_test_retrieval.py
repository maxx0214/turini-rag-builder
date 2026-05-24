import chromadb
from sentence_transformers import SentenceTransformer


VECTOR_DB_PATH = "data/vector_db"
COLLECTION_NAME = "turini_education_docs"


def search(query, n_results=3):
    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
    collection = client.get_collection(name=COLLECTION_NAME)

    model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    query_embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
    )

    return results


def print_results(query, results):
    print("\n==============================")
    print(f"검색 질문: {query}")
    print("==============================\n")

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for i, (doc, meta, distance) in enumerate(zip(documents, metadatas, distances), start=1):
        print(f"[{i}] {meta['title']}")
        print(f"카테고리: {meta['category']}")
        print(f"레벨: {meta['level']}")
        print(f"거리 점수: {distance}")
        print(f"내용: {doc[:250]}...")
        print("-" * 50)


def main():
    test_queries = [
        """
        "미국 기준금리가 뭔지 설명해줘",
        "채권 가격이랑 금리는 왜 관련 있어?",
        "CPI랑 인플레이션이 뭐야?",
        "실업률이 높아지면 경제를 어떻게 이해해야 해?",
        "GDP는 포트폴리오 이해랑 무슨 관련이 있어?",
        "미국 기준금리 흐름이 포트폴리오 공부랑 무슨 관련 있어?",
        "미국 10년물 국채금리는 채권형 자산이랑 어떻게 연결돼?",
        "CPI 흐름을 보면 뭘 공부해야 해?",
        "실업률은 경기 이해에 왜 중요해?",
        "GDP 흐름은 경제성장 개념이랑 어떻게 연결돼?",
        """##FRED용 확인 질문
        "국내 투자자들이 많이 보유한 반도체 관련 자산은 어떤 구조로 이해해야 해?",
        "SOXL 같은 반도체 레버리지 ETF는 어떤 개념을 공부해야 해?",
        "SOXS 같은 인버스 ETF는 어떤 구조야?",
        "TQQQ나 QLD 같은 나스닥 레버리지 ETF는 왜 복리효과가 중요해?",
        "SCHD 같은 배당 ETF는 어떤 구조야?",
        "SGOV 같은 초단기채 ETF는 어떻게 이해해야 해?",
        "NVDA나 AMD 같은 반도체 개별주는 어떤 리스크 개념이랑 연결돼?",
        "QQQ나 QQQM 같은 나스닥100 ETF는 성장주랑 무슨 관련이 있어?"
    ]

    for query in test_queries:
        results = search(query, n_results=3)
        print_results(query, results)


if __name__ == "__main__":
    main()