import json
from pathlib import Path
from datetime import datetime

import pandas as pd


MAPPING_PATH = Path("data/processed/popular_asset_mapping.csv")
PRICE_PATH = Path("data/processed/yfinance_prices.csv")
OUTPUT_DIR = Path("data/rag_docs/draft")


GROUP_DOC_INFO = {
    "semiconductor_stock": {
        "doc_id": "yf_popular_semiconductor_stock_001",
        "title": "국내 투자자 인기 해외자산에서 나타나는 반도체 개별주 집중 구조",
        "category": "개별주식",
        "level": 3,
        "keywords": ["반도체", "개별주식", "집중도", "섹터", "변동성"],
        "related_quiz_tags": ["반도체", "개별주식", "섹터 집중", "변동성"],
        "concepts": ["섹터 집중도", "개별주식 리스크", "반도체 사이클", "변동성"],
    },
    "semiconductor_etf": {
        "doc_id": "yf_popular_semiconductor_etf_001",
        "title": "국내 투자자 인기 해외자산에서 나타나는 반도체 ETF 구조",
        "category": "ETF",
        "level": 3,
        "keywords": ["반도체 ETF", "섹터 ETF", "분산투자", "SOXX", "변동성"],
        "related_quiz_tags": ["ETF", "반도체", "섹터 ETF", "분산투자"],
        "concepts": ["섹터 ETF", "분산투자", "섹터 집중", "변동성"],
    },
    "semiconductor_leverage_etf": {
        "doc_id": "yf_popular_semiconductor_leverage_001",
        "title": "국내 투자자 인기 해외자산에서 나타나는 반도체 레버리지 ETF 구조",
        "category": "레버리지 ETF",
        "level": 4,
        "keywords": ["SOXL", "반도체 레버리지", "레버리지 ETF", "복리효과", "변동성"],
        "related_quiz_tags": ["레버리지", "ETF", "반도체", "복리효과"],
        "concepts": ["레버리지 ETF", "일일 수익률", "복리효과", "변동성 확대"],
    },
    "semiconductor_inverse_etf": {
        "doc_id": "yf_popular_semiconductor_inverse_001",
        "title": "국내 투자자 인기 해외자산에서 나타나는 반도체 인버스 ETF 구조",
        "category": "인버스 ETF",
        "level": 4,
        "keywords": ["SOXS", "인버스 ETF", "반도체", "역방향", "레버리지"],
        "related_quiz_tags": ["인버스", "레버리지", "ETF", "반도체"],
        "concepts": ["인버스 ETF", "역방향 수익률", "레버리지", "복리효과"],
    },
    "nasdaq100_etf": {
        "doc_id": "yf_popular_nasdaq100_etf_001",
        "title": "국내 투자자 인기 해외자산에서 나타나는 나스닥100 ETF 구조",
        "category": "ETF",
        "level": 3,
        "keywords": ["QQQ", "QQQM", "나스닥100", "성장주", "기술주"],
        "related_quiz_tags": ["나스닥100", "ETF", "성장주", "기술주"],
        "concepts": ["나스닥100", "성장주", "기술주 비중", "지수추종"],
    },
    "nasdaq100_leverage_etf": {
        "doc_id": "yf_popular_nasdaq100_leverage_001",
        "title": "국내 투자자 인기 해외자산에서 나타나는 나스닥100 레버리지 ETF 구조",
        "category": "레버리지 ETF",
        "level": 4,
        "keywords": ["TQQQ", "QLD", "나스닥100", "레버리지 ETF", "복리효과"],
        "related_quiz_tags": ["레버리지", "나스닥100", "ETF", "복리효과"],
        "concepts": ["레버리지 ETF", "일일 수익률", "복리효과", "변동성"],
    },
    "sp500_etf": {
        "doc_id": "yf_popular_sp500_etf_001",
        "title": "국내 투자자 인기 해외자산에서 나타나는 S&P500 ETF 구조",
        "category": "ETF",
        "level": 2,
        "keywords": ["VOO", "S&P500", "미국 대형주", "지수추종", "분산투자"],
        "related_quiz_tags": ["S&P500", "ETF", "분산투자", "지수추종"],
        "concepts": ["S&P500", "미국 대형주", "분산투자", "시장대표성"],
    },
    "dividend_etf": {
        "doc_id": "yf_popular_dividend_etf_001",
        "title": "국내 투자자 인기 해외자산에서 나타나는 배당 ETF 구조",
        "category": "ETF",
        "level": 2,
        "keywords": ["SCHD", "배당 ETF", "분배금", "현금흐름", "배당주"],
        "related_quiz_tags": ["배당", "ETF", "현금흐름", "분배금"],
        "concepts": ["배당", "분배금", "현금흐름", "배당 ETF"],
    },
    "short_treasury_etf": {
        "doc_id": "yf_popular_short_treasury_001",
        "title": "국내 투자자 인기 해외자산에서 나타나는 초단기채 ETF 구조",
        "category": "채권",
        "level": 3,
        "keywords": ["SGOV", "초단기채", "미국 국채", "현금성 자산", "금리"],
        "related_quiz_tags": ["채권", "초단기채", "금리", "현금성 자산"],
        "concepts": ["초단기채", "채권 ETF", "금리", "현금성 자산"],
    },
    "bigtech_stock": {
        "doc_id": "yf_popular_bigtech_stock_001",
        "title": "국내 투자자 인기 해외자산에서 나타나는 빅테크 개별주 구조",
        "category": "개별주식",
        "level": 3,
        "keywords": ["빅테크", "개별주식", "성장주", "기술주", "집중도"],
        "related_quiz_tags": ["빅테크", "개별주식", "성장주", "집중도"],
        "concepts": ["개별주식", "성장주", "기술주", "집중도"],
    },
    "growth_stock": {
        "doc_id": "yf_popular_growth_stock_001",
        "title": "국내 투자자 인기 해외자산에서 나타나는 성장주 개별주 구조",
        "category": "개별주식",
        "level": 3,
        "keywords": ["성장주", "개별주식", "변동성", "집중투자", "미래 기대"],
        "related_quiz_tags": ["성장주", "개별주식", "변동성", "집중도"],
        "concepts": ["성장주", "개별주식", "변동성", "집중도"],
    },
    "single_stock_leverage_etf": {
        "doc_id": "yf_popular_single_stock_leverage_001",
        "title": "국내 투자자 인기 해외자산에서 나타나는 단일종목 레버리지 ETF 구조",
        "category": "레버리지 ETF",
        "level": 4,
        "keywords": ["단일종목 레버리지", "TSLL", "레버리지 ETF", "일일 수익률", "변동성"],
        "related_quiz_tags": ["레버리지", "단일종목 ETF", "복리효과", "변동성"],
        "concepts": ["단일종목 레버리지 ETF", "일일 수익률", "복리효과", "변동성"],
    },
    "quantum_stock": {
        "doc_id": "yf_popular_quantum_stock_001",
        "title": "국내 투자자 인기 해외자산에서 나타나는 테마형 개별주 구조",
        "category": "개별주식",
        "level": 4,
        "keywords": ["테마주", "양자컴퓨팅", "개별주식", "성장 기대", "변동성"],
        "related_quiz_tags": ["테마주", "개별주식", "변동성", "집중도"],
        "concepts": ["테마형 개별주", "기대 기반 가격 변동", "변동성", "집중도"],
    },
    "bitcoin_related_stock": {
        "doc_id": "yf_popular_bitcoin_related_stock_001",
        "title": "국내 투자자 인기 해외자산에서 나타나는 비트코인 관련주 구조",
        "category": "개별주식",
        "level": 4,
        "keywords": ["비트코인 관련주", "MSTR", "대체자산", "개별주식", "변동성"],
        "related_quiz_tags": ["비트코인", "관련주", "대체자산", "변동성"],
        "concepts": ["비트코인 관련주", "대체자산 노출", "개별주식", "변동성"],
    },
}


def load_data():
    if not MAPPING_PATH.exists():
        raise FileNotFoundError(f"{MAPPING_PATH} 파일이 없습니다.")

    if not PRICE_PATH.exists():
        raise FileNotFoundError(f"{PRICE_PATH} 파일이 없습니다. 먼저 02_collect_yfinance.py를 실행하세요.")

    mapping_df = pd.read_csv(MAPPING_PATH)
    price_df = pd.read_csv(PRICE_PATH)

    required_mapping_cols = {"rank", "name", "amount", "ticker", "asset_group"}
    missing_mapping = required_mapping_cols - set(mapping_df.columns)
    if missing_mapping:
        raise ValueError(f"popular_asset_mapping.csv에 필요한 컬럼이 없습니다: {missing_mapping}")

    if "ticker" not in price_df.columns:
        raise ValueError("yfinance_prices.csv에 ticker 컬럼이 없습니다.")

    possible_date_cols = ["Date", "date", "Datetime", "datetime", "Price", "Unnamed: 0"]

    date_col = None

    for col in possible_date_cols:
        if col in price_df.columns:
            date_col = col
            break

    if date_col is None:
        raise ValueError(
        f"yfinance_prices.csv에 날짜 컬럼이 없습니다. 현재 컬럼: {price_df.columns.tolist()}"
    )

    possible_price_cols = ["Adj Close", "Close", "close", "price"]

    price_col = None

    for col in possible_price_cols:
        if col in price_df.columns:
            price_col = col
            break

    if price_col is None:
        raise ValueError(
            f"yfinance_prices.csv에 가격 컬럼이 없습니다. 현재 컬럼: {price_df.columns.tolist()}"
        )

    price_df = price_df.rename(columns={date_col: "date", price_col: "price"})
    price_df["date"] = pd.to_datetime(price_df["date"], errors="coerce")
    price_df["price"] = pd.to_numeric(price_df["price"], errors="coerce")
    price_df = price_df.dropna(subset=["date", "price", "ticker"])

    return mapping_df, price_df


def calculate_mdd(price_series):
    cumulative_max = price_series.cummax()
    drawdown = price_series / cumulative_max - 1
    return drawdown.min()


def get_ticker_metrics(price_df, ticker):
    target = price_df[price_df["ticker"] == ticker].sort_values("date").copy()

    if target.empty:
        return None

    target["daily_return"] = target["price"].pct_change()

    latest = target.iloc[-1]
    latest_date = latest["date"]
    latest_price = latest["price"]

    one_year_ago = latest_date - pd.DateOffset(years=1)
    one_year_data = target[target["date"] >= one_year_ago].copy()

    if len(one_year_data) < 2:
        return None

    start_price = one_year_data.iloc[0]["price"]
    return_1y = latest_price / start_price - 1
    annualized_volatility = one_year_data["daily_return"].std() * (252 ** 0.5)
    mdd = calculate_mdd(one_year_data["price"])

    return {
        "ticker": ticker,
        "latest_date": latest_date.strftime("%Y-%m-%d"),
        "latest_price": round(float(latest_price), 4),
        "return_1y": round(float(return_1y), 4),
        "annualized_volatility": round(float(annualized_volatility), 4),
        "mdd": round(float(mdd), 4),
    }


def format_percent(value):
    if value is None or pd.isna(value):
        return "데이터 제한"
    return f"{value * 100:.2f}%"


def summarize_group(mapping_df, price_df, asset_group):
    group_assets = mapping_df[mapping_df["asset_group"] == asset_group].copy()

    metrics = []

    for ticker in group_assets["ticker"].dropna().unique():
        metric = get_ticker_metrics(price_df, ticker)
        if metric:
            metrics.append(metric)

    metrics_df = pd.DataFrame(metrics)

    if metrics_df.empty:
        avg_return_1y = None
        avg_volatility = None
        avg_mdd = None
        latest_date = None
    else:
        avg_return_1y = metrics_df["return_1y"].mean()
        avg_volatility = metrics_df["annualized_volatility"].mean()
        avg_mdd = metrics_df["mdd"].mean()
        latest_date = metrics_df["latest_date"].max()

    top_assets = group_assets.sort_values("rank").head(5)

    return {
        "asset_group": asset_group,
        "asset_count": int(len(group_assets)),
        "tickers": group_assets["ticker"].dropna().astype(str).tolist(),
        "top_assets": [
            {
                "rank": int(row["rank"]),
                "ticker": str(row["ticker"]),
                "name": str(row["name"]),
                "amount": int(row["amount"]),
            }
            for _, row in top_assets.iterrows()
        ],
        "latest_date": latest_date,
        "avg_return_1y": None if avg_return_1y is None else round(float(avg_return_1y), 4),
        "avg_annualized_volatility": None if avg_volatility is None else round(float(avg_volatility), 4),
        "avg_mdd": None if avg_mdd is None else round(float(avg_mdd), 4),
    }


def make_summary_text(summary):
    tickers = ", ".join(summary["tickers"])
    return (
        f"이 자산군에는 TOP 50 매핑 기준 {summary['asset_count']}개 자산이 포함되어 있으며, "
        f"대표 티커는 {tickers}입니다. "
        f"yfinance 가격 데이터 기준 최근 1년 평균 가격 변화율은 {format_percent(summary['avg_return_1y'])}, "
        f"평균 연율화 변동성은 {format_percent(summary['avg_annualized_volatility'])}, "
        f"평균 최대낙폭은 {format_percent(summary['avg_mdd'])}입니다."
    )


def make_doc(asset_group, info, summary):
    concepts = ", ".join(info["concepts"])
    summary_text = make_summary_text(summary)

    content = (
        f"이 문서는 대한민국 투자자 인기 해외자산 TOP 50에서 '{asset_group}' 유형으로 분류된 자산을 바탕으로 만든 학습 문서이다. "
        f"{summary_text} "
        f"이 자산군은 {concepts} 같은 개념을 학습할 때 활용할 수 있다. "
        f"특히 가격 변화율은 과거 가격 흐름을, 변동성은 가격이 얼마나 크게 흔들렸는지를, 최대낙폭은 특정 기간 동안 고점 대비 하락 경험을 이해하는 데 도움을 준다. "
        f"다만 이 데이터는 학습용 참고자료이며, 특정 종목이나 ETF의 좋고 나쁨을 판단하거나 미래 수익률을 예측하기 위한 자료가 아니다. "
        f"Turini에서는 이 문서를 사용자의 포트폴리오에 포함된 자산군을 설명하고 관련 학습 주제와 퀴즈를 연결하는 용도로만 사용한다."
    )

    return {
        "doc_id": info["doc_id"],
        "title": info["title"],
        "category": info["category"],
        "level": info["level"],
        "asset_group": asset_group,
        "keywords": info["keywords"],
        "related_data": ["yfinance", "popular_asset_mapping"],
        "related_portfolio_features": [
            f"{asset_group} 유형 자산 포함",
            "해외자산 포함",
            "국내 투자자 인기 해외자산과 유사한 구조",
        ],
        "related_quiz_tags": info["related_quiz_tags"],
        "content": content,
        "data_snapshot": {
            "source": "yfinance",
            "mapping_source": "korea_popular_assets_top50",
            "asset_group": asset_group,
            "asset_count": summary["asset_count"],
            "tickers": summary["tickers"],
            "top_assets": summary["top_assets"],
            "latest_date": summary["latest_date"],
            "avg_return_1y": summary["avg_return_1y"],
            "avg_annualized_volatility": summary["avg_annualized_volatility"],
            "avg_mdd": summary["avg_mdd"],
            "usage_note": (
                "이 데이터는 자산군 구조와 리스크 개념을 이해하기 위한 학습용 참고자료이며 "
                "투자 판단이나 수익률 예측에 사용하지 않는다."
            ),
        },
        "safe_response_rule": (
            "특정 종목, ETF, 자산의 매수·매도·보유 판단이나 미래 수익률 예측이 아니라 "
            "자산군 구조 설명과 학습 경로 추천에만 사용한다."
        ),
        "source": "yfinance",
        "doc_type": "popular_asset_group_data_connection",
        "updated_at": datetime.now().strftime("%Y-%m-%d"),
    }


def main():
    mapping_df, price_df = load_data()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    created_count = 0

    for asset_group, info in GROUP_DOC_INFO.items():
        if asset_group not in mapping_df["asset_group"].unique():
            print(f"[건너뜀] {asset_group}: mapping에 없음")
            continue

        summary = summarize_group(mapping_df, price_df, asset_group)
        doc = make_doc(asset_group, info, summary)

        output_path = OUTPUT_DIR / f"{doc['doc_id']}.json"

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)

        created_count += 1
        print(f"저장 완료: {output_path}")

    print(f"\n인기 해외자산 기반 yfinance 문서 생성 완료: {created_count}개")
    print(f"저장 위치: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()