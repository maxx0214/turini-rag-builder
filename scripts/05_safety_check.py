import json
import shutil
from pathlib import Path


DRAFT_DIR = Path("data/rag_docs/draft")
FINAL_DIR = Path("data/rag_docs/final")
REVIEW_DIR = Path("data/rag_docs/review_required")


BANNED_PHRASES = [
    "추천합니다",
    "추천할 수 있습니다",
    "매수",
    "매도",
    "보유하세요",
    "사야",
    "팔아야",
    "좋은 종목",
    "나쁜 종목",
    "유망",
    "수익률이 높",
    "수익률이 낮",
    "오를 가능성",
    "떨어질 가능성",
    "상승할 가능성",
    "하락할 가능성",
    "투자하기 좋",
    "피하는 것이 좋",
    "적합한 투자",
    "부적합한 투자",
    "수익을 기대",
    "손실을 피",
]


REQUIRED_FIELDS = [
    "doc_id",
    "title",
    "category",
    "level",
    "keywords",
    "related_data",
    "related_portfolio_features",
    "related_quiz_tags",
    "content",
    "safe_response_rule",
    "source",
    "updated_at",
]


def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_required_fields(doc):
    missing = []

    for field in REQUIRED_FIELDS:
        if field not in doc:
            missing.append(field)

    return missing


def check_banned_phrases(doc):
    text_parts = []

    # safe_response_rule은 "매수·매도 금지" 같은 문구를 포함하므로 금지어 검사 대상에서 제외
    for key in ["title", "content"]:
        value = doc.get(key, "")
        if isinstance(value, str):
            text_parts.append(value)

    text = "\n".join(text_parts)

    detected = []

    for phrase in BANNED_PHRASES:
        if phrase in text:
            detected.append(phrase)

    return detected


def check_doc(doc):
    issues = []

    missing_fields = check_required_fields(doc)
    if missing_fields:
        issues.append({
            "type": "missing_fields",
            "items": missing_fields,
        })

    banned_phrases = check_banned_phrases(doc)
    if banned_phrases:
        issues.append({
            "type": "banned_phrases",
            "items": banned_phrases,
        })

    content = doc.get("content", "")
    if len(content) < 100:
        issues.append({
            "type": "content_too_short",
            "items": [f"content length: {len(content)}"],
        })

    safe_rule = doc.get("safe_response_rule", "")

    required_safe_terms = ["매수", "매도", "수익률 예측"]

    missing_safe_terms = [
        term for term in required_safe_terms
        if term not in safe_rule
    ]

    if missing_safe_terms:
        issues.append({
            "type": "safe_rule_weak",
            "items": [f"safe_response_rule에 필요한 제한 문구가 부족합니다: {missing_safe_terms}"],
        })

    return issues


def main():
    if not DRAFT_DIR.exists():
        raise FileNotFoundError(f"{DRAFT_DIR} 폴더가 없습니다.")

    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)

    json_files = list(DRAFT_DIR.glob("*.json"))

    if not json_files:
        print("검사할 JSON 문서가 없습니다.")
        return

    passed_count = 0
    review_count = 0

    for file_path in json_files:
        doc = load_json(file_path)
        issues = check_doc(doc)

        if issues:
            review_count += 1
            target_path = REVIEW_DIR / file_path.name
            shutil.copy2(file_path, target_path)

            print(f"[검토 필요] {file_path.name}")
            for issue in issues:
                print(f"  - {issue['type']}: {issue['items']}")

        else:
            passed_count += 1
            target_path = FINAL_DIR / file_path.name
            shutil.copy2(file_path, target_path)

            print(f"[통과] {file_path.name}")

    print("\n안전 검사 완료")
    print(f"통과: {passed_count}개")
    print(f"검토 필요: {review_count}개")
    print(f"통과 문서 위치: {FINAL_DIR}")
    print(f"검토 문서 위치: {REVIEW_DIR}")


if __name__ == "__main__":
    main()