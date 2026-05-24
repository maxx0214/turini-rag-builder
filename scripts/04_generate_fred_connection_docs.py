import json
from pathlib import Path
from datetime import datetime

import pandas as pd


INPUT_PATH = Path("data/processed/fred_indicators.csv")
OUTPUT_DIR = Path("data/rag_docs/draft")


def load_fred_data():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"{INPUT_PATH} 파일이 없습니다. 먼저 scripts/01_collect_fred.py를 실행하세요."
        )

    df = pd.read_csv(INPUT_PATH)

    required_cols = {"date", "series_id", "series_name", "value", "source"}
    missing = required_cols - set(df.columns)

    if missing:
        raise ValueError(f"fred_indicators.csv에 필요한 컬럼이 없습니다: {missing}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["date", "value"])

    return df


def get_snapshot(df, series_id):
    target = df[df["series_id"] == series_id].sort_values("date")

    if target.empty:
        return {
            "series_id": series_id,
            "latest_date": None,
            "latest_value": None,
            "change_1y": None,
            "trend_label": "데이터 없음",
        }

    latest = target.iloc[-1]
    latest_date = latest["date"]
    latest_value = latest["value"]

    one_year_ago = latest_date - pd.DateOffset(years=1)
    past = target[target["date"] <= one_year_ago]

    if past.empty:
        change_1y = None
        trend_label = "최근 추세 판단 제한"
    else:
        past_value = past.iloc[-1]["value"]
        change_1y = latest_value - past_value

        if change_1y > 0:
            trend_label = "1년 전보다 상승"
        elif change_1y < 0:
            trend_label = "1년 전보다 하락"
        else:
            trend_label = "1년 전과 유사"

    return {
        "series_id": series_id,
        "latest_date": latest_date.strftime("%Y-%m-%d"),
        "latest_value": round(float(latest_value), 4),
        "change_1y": None if change_1y is None else round(float(change_1y), 4),
        "trend_label": trend_label,
    }


def format_snapshot_text(snapshot, unit_label):
    latest_date = snapshot.get("latest_date")
    latest_value = snapshot.get("latest_value")
    change_1y = snapshot.get("change_1y")
    trend_label = snapshot.get("trend_label")

    if latest_date is None or latest_value is None:
        return "현재 사용할 수 있는 최신 데이터가 제한적입니다."

    change_text = "1년 변화 데이터는 제한적입니다."
    if change_1y is not None:
        if change_1y > 0:
            change_text = f"1년 전보다 {abs(change_1y)}{unit_label} 높습니다."
        elif change_1y < 0:
            change_text = f"1년 전보다 {abs(change_1y)}{unit_label} 낮습니다."
        else:
            change_text = f"1년 전과 거의 같은 수준입니다."

    return (
        f"최신 관측일은 {latest_date}이고, 최신값은 {latest_value}{unit_label}입니다. "
        f"{change_text} 추세 라벨은 '{trend_label}'입니다."
    )


def make_connection_doc(
    doc_id,
    title,
    category,
    level,
    keywords,
    related_data,
    related_portfolio_features,
    related_quiz_tags,
    content,
    snapshot,
    unit_label,
):
    return {
        "doc_id": doc_id,
        "title": title,
        "category": category,
        "level": level,
        "keywords": keywords,
        "related_data": related_data,
        "related_portfolio_features": related_portfolio_features,
        "related_quiz_tags": related_quiz_tags,
        "content": content,
        "data_snapshot": {
            "source": "FRED",
            "source_series_id": snapshot.get("series_id"),
            "latest_date": snapshot.get("latest_date"),
            "latest_value": snapshot.get("latest_value"),
            "unit_label": unit_label,
            "change_1y": snapshot.get("change_1y"),
            "trend_label": snapshot.get("trend_label"),
            "snapshot_text": format_snapshot_text(snapshot, unit_label),
            "usage_note": (
                "이 데이터는 경제 개념과 포트폴리오 구조를 이해하기 위한 학습용 참고자료이다. "
                "특정 종목, ETF, 자산의 좋고 나쁨을 판단하거나 미래 수익률을 예측하는 데 사용하지 않는다."
            ),
        },
        "safe_response_rule": (
            "특정 종목, ETF, 자산의 매수·매도·보유 판단이나 미래 수익률 예측이 아니라 "
            "경제 개념 설명과 학습 경로 추천에만 사용한다."
        ),
        "source": "FRED",
        "doc_type": "data_connection",
        "updated_at": datetime.now().strftime("%Y-%m-%d"),
    }


def build_docs(df):
    snapshots = {
        "FEDFUNDS": get_snapshot(df, "FEDFUNDS"),
        "DGS10": get_snapshot(df, "DGS10"),
        "CPIAUCSL": get_snapshot(df, "CPIAUCSL"),
        "UNRATE": get_snapshot(df, "UNRATE"),
        "GDP": get_snapshot(df, "GDP"),
    }

    fedfunds_snapshot = format_snapshot_text(snapshots["FEDFUNDS"], "%")
    dgs10_snapshot = format_snapshot_text(snapshots["DGS10"], "%")
    cpi_snapshot = format_snapshot_text(snapshots["CPIAUCSL"], " index")
    unrate_snapshot = format_snapshot_text(snapshots["UNRATE"], "%")
    gdp_snapshot = format_snapshot_text(snapshots["GDP"], " billion dollars")

    docs = []

    docs.append(make_connection_doc(
        doc_id="fred_connection_fedfunds_001",
        title="최근 미국 기준금리 흐름과 연결되는 개념",
        category="시장환경",
        level=3,
        keywords=[
            "미국 기준금리",
            "FEDFUNDS",
            "금리 흐름",
            "자금조달 비용",
            "통화정책",
        ],
        related_data=["FEDFUNDS"],
        related_portfolio_features=[
            "미국 ETF 비중 높음",
            "성장주 자산 비중 높음",
            "채권형 자산 포함",
            "현금 비중 높음",
        ],
        related_quiz_tags=["금리", "통화정책", "자금조달 비용", "미국경제"],
        content=(
            f"FRED의 FEDFUNDS 데이터는 미국 기준금리의 흐름을 이해하는 데 활용할 수 있다. "
            f"{fedfunds_snapshot} "
            f"이 흐름은 기준금리, 자금조달 비용, 채권금리, 현금성 자산, 성장주 변동성 같은 개념과 연결해서 학습할 수 있다. "
            f"예를 들어 기준금리 수준을 보면 돈을 빌리는 비용과 시장금리의 기본 구조를 이해하는 데 도움이 된다. "
            f"다만 기준금리 데이터는 경제 개념을 이해하기 위한 참고자료이며, 특정 자산의 좋고 나쁨이나 미래 성과를 판단하는 기준으로 사용해서는 안 된다."
        ),
        snapshot=snapshots["FEDFUNDS"],
        unit_label="%",
    ))

    docs.append(make_connection_doc(
        doc_id="fred_connection_dgs10_001",
        title="미국 10년물 국채금리와 채권형 자산 이해",
        category="시장환경",
        level=3,
        keywords=[
            "미국 10년물 국채금리",
            "DGS10",
            "장기금리",
            "채권 가격",
            "채권형 자산",
        ],
        related_data=["DGS10"],
        related_portfolio_features=[
            "채권형 자산 포함",
            "장기채 ETF 포함",
            "미국 ETF 비중 높음",
            "안정형 포트폴리오",
        ],
        related_quiz_tags=["채권", "장기금리", "금리와 채권 가격", "미국경제"],
        content=(
            f"FRED의 DGS10 데이터는 미국 10년물 국채금리의 흐름을 보여준다. "
            f"{dgs10_snapshot} "
            f"이 지표는 장기금리, 채권 가격, 듀레이션, 채권형 ETF 구조를 이해할 때 자주 연결된다. "
            f"채권 가격과 시장금리는 일반적으로 반대 방향으로 움직이는 경향이 있기 때문에, 장기금리 흐름을 보면 채권형 자산이 왜 가격 변동을 경험할 수 있는지 학습하는 데 도움이 된다. "
            f"단, 이 문서는 채권형 자산의 구조를 이해하기 위한 것이며 특정 자산의 투자 판단을 제공하지 않는다."
        ),
        snapshot=snapshots["DGS10"],
        unit_label="%",
    ))

    docs.append(make_connection_doc(
        doc_id="fred_connection_cpi_001",
        title="CPI 흐름과 인플레이션 학습 포인트",
        category="시장환경",
        level=2,
        keywords=[
            "CPI",
            "소비자물가지수",
            "인플레이션",
            "구매력",
            "물가 흐름",
        ],
        related_data=["CPIAUCSL"],
        related_portfolio_features=[
            "현금 비중 높음",
            "채권형 자산 포함",
            "미국 ETF 비중 높음",
            "안정형 포트폴리오",
        ],
        related_quiz_tags=["CPI", "인플레이션", "구매력", "경제지표"],
        content=(
            f"FRED의 CPIAUCSL 데이터는 미국 소비자물가지수 흐름을 이해하는 데 사용할 수 있다. "
            f"{cpi_snapshot} "
            f"CPI는 인플레이션, 구매력, 실질수익률, 금리 변화와 연결되는 핵심 지표이다. "
            f"물가가 변하면 같은 금액으로 살 수 있는 상품과 서비스의 양이 달라질 수 있기 때문에, 현금 보유와 실질 구매력 개념을 함께 학습하는 데 도움이 된다. "
            f"이 데이터는 물가 개념을 이해하기 위한 자료이며, 특정 자산의 방향이나 수익률을 예측하기 위한 자료가 아니다."
        ),
        snapshot=snapshots["CPIAUCSL"],
        unit_label=" index",
    ))

    docs.append(make_connection_doc(
        doc_id="fred_connection_unrate_001",
        title="실업률 흐름과 경기 이해",
        category="시장환경",
        level=2,
        keywords=[
            "실업률",
            "UNRATE",
            "고용",
            "경기 흐름",
            "소비",
        ],
        related_data=["UNRATE"],
        related_portfolio_features=[
            "미국 ETF 비중 높음",
            "주식형 자산 비중 높음",
            "경기민감 자산 포함",
        ],
        related_quiz_tags=["실업률", "고용", "경기", "미국경제"],
        content=(
            f"FRED의 UNRATE 데이터는 미국 실업률 흐름을 보여준다. "
            f"{unrate_snapshot} "
            f"실업률은 고용 상황, 소비 여건, 경기 흐름을 이해하는 데 사용되는 대표적인 경제지표이다. "
            f"포트폴리오 학습에서는 실업률을 통해 경기 둔화, 기업 활동, 소비 환경 같은 개념을 연결해서 이해할 수 있다. "
            f"하지만 실업률 하나만으로 특정 자산의 적절성이나 미래 성과를 판단해서는 안 된다."
        ),
        snapshot=snapshots["UNRATE"],
        unit_label="%",
    ))

    docs.append(make_connection_doc(
        doc_id="fred_connection_gdp_001",
        title="GDP 흐름과 경제성장 이해",
        category="시장환경",
        level=2,
        keywords=[
            "GDP",
            "경제성장",
            "국내총생산",
            "경기 흐름",
            "생산과 소비",
        ],
        related_data=["GDP"],
        related_portfolio_features=[
            "미국 ETF 비중 높음",
            "주식형 자산 비중 높음",
            "경기민감 자산 포함",
            "장기 투자 학습",
        ],
        related_quiz_tags=["GDP", "경제성장", "경기", "미국경제"],
        content=(
            f"FRED의 GDP 데이터는 미국 경제의 생산 규모와 성장 흐름을 이해하는 데 활용할 수 있다. "
            f"{gdp_snapshot} "
            f"GDP는 경제성장률, 경기 흐름, 기업 활동, 소비와 투자 환경을 이해할 때 기본이 되는 지표이다. "
            f"포트폴리오 학습에서는 GDP를 통해 자산 가격을 예측하기보다, 경제 전체의 활동 수준이 어떤 의미를 가지는지 이해하는 데 초점을 둔다. "
            f"따라서 이 문서는 경제성장 개념을 설명하기 위한 것이며 특정 자산을 평가하거나 수익률을 예측하지 않는다."
        ),
        snapshot=snapshots["GDP"],
        unit_label=" billion dollars",
    ))

    return docs


def save_docs(docs):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for doc in docs:
        file_path = OUTPUT_DIR / f"{doc['doc_id']}.json"

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)

        print(f"저장 완료: {file_path}")


def main():
    df = load_fred_data()
    docs = build_docs(df)
    save_docs(docs)

    print(f"\nFRED 데이터 연결 문서 생성 완료: {len(docs)}개")
    print(f"저장 위치: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()