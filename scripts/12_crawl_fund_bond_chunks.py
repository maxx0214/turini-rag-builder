import hashlib
import json
import re
import time
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


OUTPUT_DIR = Path("data/export")
RAW_DIR = Path("data/raw/fund_bond")

OUTPUT_JSONL_PATH = OUTPUT_DIR / "chunks_fund_bond.jsonl"
OUTPUT_JSON_PATH = OUTPUT_DIR / "chunks_fund_bond.json"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

PUBLISHED_DATE = str(date.today())

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}


SOURCES = [
    {
        "source_name": "KCIE",
        "source_url": "https://www.kcie.or.kr/guide/3/18/web_view?content_idx=518",
        "title": "ETF 성공투자를 위해서는 꼭 알아두어야 할 용어들",
        "topic": "fund",
        "published_date": "2019-07-05",
    },
    {
        "source_name": "KCIE",
        "source_url": "https://www.kcie.or.kr/mobile/guide/2/25/web_view?content_idx=1149&series_idx=",
        "title": "ETF와 ETN 차이",
        "topic": "fund",
        "published_date": PUBLISHED_DATE,
    },
    {
        "source_name": "KCIE",
        "source_url": "https://www.kcie.or.kr/yeouitv/deundeunWebBook/web_view?content_idx=2062&menu_idx=256",
        "title": "펀드와 ETF의 원금손실 위험과 분산투자",
        "topic": "fund",
        "published_date": "2025-08-05",
    },
    {
        "source_name": "KDI",
        "source_url": "https://eiec.kdi.re.kr/material/clickView.do?cidx=1670&click_yymm=201512",
        "title": "채권수익률과 가격결정",
        "topic": "bond",
        "published_date": "2015-12-01",
    },
    {
        "source_name": "KRX",
        "source_url": "https://sribond.krx.co.kr/contents/01/01010000/SRI01010000.jsp",
        "title": "ESG채권의 종류",
        "topic": "bond",
        "published_date": PUBLISHED_DATE,
    },
]


REMOVE_SELECTORS = [
    "script",
    "style",
    "noscript",
    "header",
    "footer",
    "nav",
    "aside",
    "form",
    "button",
    "iframe",
]


NOISE_PATTERNS = [
    r"MY콘텐츠담기",
    r"메인 페이지 바로가기",
    r"대메뉴 바로가기",
    r"본문 바로가기",
    r"본문으로 바로가기",
    r"TOP",
    r"로그인",
    r"회원가입",
    r"공유하기",
    r"목록",
    r"이전글",
    r"다음글",
    r"개인정보처리방침",
    r"저작권",
    r"Copyright",
    r"회별별점",
    r"별점주기",
    r"댓글작성",
    r"댓글입력",
    r"댓글등록",
    r"맨위로",
    r"목록보기",
    r"팝업 닫기",
    r"URL 복사",
    r"콘텐츠 만족도",
]


MENU_TEXT_TERMS = [
    "알고 투자하면 꿈이 커집니다",
    "Korea Council for Investor Education",
    "최신콘텐츠",
    "찾아가는 연금",
    "금융투자 HOWTO",
    "군장병 금융투자",
    "MZ 머니",
    "자립준비청년을 위한 든든한 금융",
    "투자&세테크",
    "1:1 자산관리법",
    "투자 이야기",
    "실전투자 Insight",
    "온라인 스쿨",
    "연금 스쿨",
    "ETF 스쿨",
    "생애자산관리스쿨",
    "대체투자스쿨",
    "파생상품스쿨",
    "시니어 디지털 금융스쿨",
    "투자가이드",
    "생애자산관리",
    "증권투자",
    "펀드투자",
    "연금관리",
    "세제&절세",
    "투자 Tip",
    "초보투자자 길라잡이",
    "기타 콘텐츠",
    "늘봄교육",
    "파이낸셜 빌리지",
    "모의투자게임",
    "경제버스",
    "금융투자 뮤지컬",
    "온라인 교원연수",
    "투교협 소개",
    "인사말",
    "주요 사업",
    "오시는 길",
    "공지사항",
    "상담 연락처",
    "다양한 금융투자 가이드",
    "아는 만큼 보이는 투자의 길",
    "English",
]


ARTICLE_START_PATTERNS = [
    r"\[출처",
    r"ETF\s*\(\s*Exchange\s+Traded\s+Fund\s*\)",
    r"ETF\s*는",
    r"E\s*로 시작되는 금융상품",
    r"펀드\s*는",
    r"펀드란",
    r"채권\s*은",
    r"채권수익률",
    r"채권의 가격",
    r"ESG채권이란\?",
    r"ESG채권\s*은",
    r"녹색채권",
]


ARTICLE_END_PATTERNS = [
    r"회별별점",
    r"별점주기",
    r"댓글작성",
    r"댓글입력",
    r"댓글등록",
    r"맨위로",
    r"목록보기",
    r"공유하기",
    r"팝업 닫기",
    r"URL 복사",
    r"콘텐츠 만족도",
    r"이전글",
    r"다음글",
]


def make_stable_doc_id(source_name: str, url: str) -> str:
    raw = f"{source_name}:{url}"
    digest = hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]
    return f"doc_{digest}"


def fetch_html(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()

    if not response.encoding or response.encoding.lower() == "iso-8859-1":
        response.encoding = response.apparent_encoding

    return response.text


def extract_title(soup: BeautifulSoup, fallback_title: str) -> str:
    fallback_title = clean_inline_text(fallback_title)
    if fallback_title:
        return fallback_title

    h1 = soup.find("h1")
    if h1:
        title = clean_inline_text(h1.get_text(" ", strip=True))
        if title:
            return title

    h2 = soup.find("h2")
    if h2:
        title = clean_inline_text(h2.get_text(" ", strip=True))
        if title:
            return title

    if soup.title:
        title = clean_inline_text(soup.title.get_text(" ", strip=True))
        if title:
            return title

    return fallback_title


def pick_main_node(soup: BeautifulSoup):
    candidates = []

    for selector in [
        "article",
        "main",
        "#content",
        "#contents",
        ".content",
        ".contents",
        ".view",
        ".view_content",
        ".board_view",
        ".sub_content",
        ".cont",
        "body",
    ]:
        selected = soup.select(selector)
        for node in selected:
            text = node.get_text(" ", strip=True)
            if text and len(text) > 300:
                candidates.append((len(text), node))

    if not candidates:
        return soup.body or soup

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def clean_inline_text(text: str) -> str:
    text = str(text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_for_match(text: str) -> str:
    return re.sub(r"\s+", "", clean_inline_text(text)).lower()


def is_noise_line(line: str) -> bool:
    if any(re.search(pattern, line, flags=re.IGNORECASE) for pattern in NOISE_PATTERNS):
        return True

    normalized_line = normalize_for_match(line)

    for term in MENU_TEXT_TERMS:
        normalized_term = normalize_for_match(term)
        if not normalized_term:
            continue
        if normalized_line == normalized_term:
            return True
        if normalized_term in normalized_line and len(normalized_line) <= len(normalized_term) + 24:
            return True

    return False


def clean_extracted_text(text: str) -> str:
    text = str(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\xa0", " ")

    lines = []
    for line in text.split("\n"):
        line = clean_inline_text(line)

        if not line:
            continue

        if is_noise_line(line):
            continue

        if len(line) <= 1:
            continue

        lines.append(line)

    cleaned = "\n".join(lines)

    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = cleaned.strip()

    return cleaned


def find_article_start(text: str, title: str = "") -> int:
    candidates = []

    for pattern in ARTICLE_START_PATTERNS:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            candidates.append(match.start())

    if candidates:
        return min(candidates)

    if title:
        title_pattern = re.escape(clean_inline_text(title)).replace(r"\ ", r"\s+")
        title_matches = [
            match.start()
            for match in re.finditer(title_pattern, text, flags=re.IGNORECASE)
        ]
        if title_matches:
            return title_matches[-1]

    return -1


def find_article_end(text: str) -> int:
    candidates = []

    for pattern in ARTICLE_END_PATTERNS:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            candidates.append(match.start())

    if candidates:
        return min(candidates)

    return -1


def trim_to_article_body(text: str, title: str = "") -> str:
    """
    사이트 메뉴/푸터/댓글 영역을 제거하고 실제 본문 영역만 남긴다.
    KCIE, KDI, KRX 같은 교육 페이지는 본문 앞뒤에 메뉴 텍스트가 많이 붙기 때문에
    키워드 기반으로 본문 시작/끝을 보정한다.
    """
    text = clean_extracted_text(text)

    # 제목은 메뉴에도 반복될 수 있으므로 강한 본문 시작 후보를 먼저 사용한다.
    start_idx = find_article_start(text, title)
    if start_idx == -1:
        start_idx = 0

    if start_idx > 0:
        text = text[start_idx:]

    # 본문 끝 자르기
    end_idx = find_article_end(text)
    if end_idx != -1:
        text = text[:end_idx]

    lines = []
    for line in text.split("\n"):
        line = clean_inline_text(line)

        if not line:
            continue

        if is_noise_line(line):
            continue

        lines.append(line)

    return "\n".join(lines).strip()

def extract_text_from_html(html: str, fallback_title: str):
    soup = BeautifulSoup(html, "lxml")

    for selector in REMOVE_SELECTORS:
        for tag in soup.select(selector):
            tag.decompose()

    title = extract_title(soup, fallback_title)
    main_node = pick_main_node(soup)

    # 블록 단위 줄바꿈을 살리기 위해 주요 태그를 순회
    parts = []
    for tag in main_node.find_all(["h1", "h2", "h3", "h4", "p", "li", "td", "th", "div"], recursive=True):
        txt = clean_inline_text(tag.get_text(" ", strip=True))
        if txt:
            parts.append(txt)

    if not parts:
        raw_text = main_node.get_text("\n", strip=True)
    else:
        # 중복 라인 제거
        deduped = []
        seen = set()
        for part in parts:
            key = part[:120]
            if key in seen:
                continue
            seen.add(key)
            deduped.append(part)
        raw_text = "\n".join(deduped)

    cleaned = clean_extracted_text(raw_text)

    return title, cleaned


def split_text_to_chunks(text: str, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    text = clean_extracted_text(text)

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


def save_raw_text(doc_id: str, source: dict, title: str, text: str):
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    raw_path = RAW_DIR / f"{doc_id}.txt"

    content = [
        f"source_name: {source['source_name']}",
        f"source_url: {source['source_url']}",
        f"title: {title}",
        f"topic: {source['topic']}",
        f"published_date: {source['published_date']}",
        "",
        text,
    ]

    raw_path.write_text("\n".join(content), encoding="utf-8")


def crawl_source(source: dict):
    source_name = source["source_name"]
    source_url = source["source_url"]
    fallback_title = source["title"]

    print(f"[crawl] {source_name} | {fallback_title}")
    print(f"        {source_url}")

    html = fetch_html(source_url)
    title, text = extract_text_from_html(html, fallback_title)
    text = trim_to_article_body(text, title or fallback_title)
    doc_id = make_stable_doc_id(source_name, source_url)

    if len(text) < 200:
        print(f"[warning] 추출 텍스트가 너무 짧음: {len(text)} chars")

    save_raw_text(doc_id, source, fallback_title, text)

    return {
        "doc_id": doc_id,
        "source_name": source_name,
        "source_url": source_url,
        "title": fallback_title,
        "topic": source["topic"],
        "published_date": source["published_date"],
        "text": text,
    }


def build_chunks(docs):
    rows = []

    for doc in docs:
        text_chunks = split_text_to_chunks(doc["text"])
        total_chunks = len(text_chunks)

        for idx, text in enumerate(text_chunks):
            chunk_id = f"{doc['doc_id']}_c{idx:03d}"

            prev_chunk_id = None
            next_chunk_id = None

            if idx > 0:
                prev_chunk_id = f"{doc['doc_id']}_c{idx - 1:03d}"

            if idx < total_chunks - 1:
                next_chunk_id = f"{doc['doc_id']}_c{idx + 1:03d}"

            row = {
                "chunk_id": chunk_id,
                "doc_id": doc["doc_id"],
                "chunk_index": idx,
                "total_chunks": total_chunks,
                "prev_chunk_id": prev_chunk_id,
                "next_chunk_id": next_chunk_id,
                "source_name": doc["source_name"],
                "source_url": doc["source_url"],
                "title": doc["title"],
                "topic": doc["topic"],
                "published_date": doc["published_date"],
                "text": text,
                "embedding_text": f"{doc['title']}\n\n{text}",
                "char_count": len(text),
            }

            rows.append(row)

    return rows


def save_jsonl(rows):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_JSONL_PATH, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def save_json(rows):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)


def print_stats(docs, chunks):
    print("\n== crawl complete ==")
    print(f"문서 수: {len(docs)}")
    print(f"청크 수: {len(chunks)}")
    print(f"JSONL: {OUTPUT_JSONL_PATH}")
    print(f"JSON: {OUTPUT_JSON_PATH}")
    print(f"RAW: {RAW_DIR}")

    topic_count = {}
    source_count = {}

    for row in chunks:
        topic_count[row["topic"]] = topic_count.get(row["topic"], 0) + 1
        source_count[row["source_name"]] = source_count.get(row["source_name"], 0) + 1

    print("\nTopic별 청크 수:")
    for topic, count in sorted(topic_count.items()):
        print(f"- {topic}: {count}")

    print("\nSource별 청크 수:")
    for source_name, count in sorted(source_count.items()):
        print(f"- {source_name}: {count}")

    if chunks:
        print("\n첫 번째 청크 예시:")
        print(json.dumps(chunks[0], ensure_ascii=False, indent=2))


def main():
    docs = []

    for source in SOURCES:
        try:
            doc = crawl_source(source)
            docs.append(doc)
            time.sleep(1)
        except Exception as e:
            print(f"[error] crawl failed: {source['source_url']}")
            print(f"        {type(e).__name__}: {e}")

    if not docs:
        raise RuntimeError("크롤링에 성공한 문서가 없습니다.")

    chunks = build_chunks(docs)

    if not chunks:
        raise RuntimeError("생성된 청크가 없습니다.")

    save_jsonl(chunks)
    save_json(chunks)
    print_stats(docs, chunks)


if __name__ == "__main__":
    main()
