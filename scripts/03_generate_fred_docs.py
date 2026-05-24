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


def get_latest_snapshot(df, series_id):
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


def make_doc(
    doc_id,
    title,
    category,
    level,
    keywords,
    related_data,
    related_portfolio_features,
    related_quiz_tags,
    content,
    source_series_id,
    snapshot,
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
            "source_series_id": source_series_id,
            "latest_date": snapshot.get("latest_date"),
            "latest_value": snapshot.get("latest_value"),
            "change_1y": snapshot.get("change_1y"),
            "trend_label": snapshot.get("trend_label"),
            "note": "이 수치는 경제 개념 이해를 돕는 참고용이며, 특정 자산의 투자 판단이나 수익률 예측에 사용하지 않는다.",
        },
        "safe_response_rule": "특정 종목, ETF, 자산의 매수·매도·보유 판단이나 미래 수익률 예측이 아니라 경제 개념 설명에만 사용한다.",
        "source": "FRED",
        "updated_at": datetime.now().strftime("%Y-%m-%d"),
    }


def build_docs(df):
    snapshots = {
        "FEDFUNDS": get_latest_snapshot(df, "FEDFUNDS"),
        "DGS10": get_latest_snapshot(df, "DGS10"),
        "CPIAUCSL": get_latest_snapshot(df, "CPIAUCSL"),
        "UNRATE": get_latest_snapshot(df, "UNRATE"),
        "GDP": get_latest_snapshot(df, "GDP"),
    }

    docs = []

    docs.append(make_doc(
        doc_id="macro_fedfunds_001",
        title="미국 기준금리란 무엇인가",
        category="거시경제",
        level=2,
        keywords=["미국 기준금리", "FEDFUNDS", "연준", "금리", "통화정책"],
        related_data=["FEDFUNDS"],
        related_portfolio_features=["미국 ETF 비중 높음", "채권형 자산 포함", "성장주 자산 비중 높음", "현금 비중 높음"],
        related_quiz_tags=["금리", "거시경제", "미국경제"],
        content=(
            "미국 기준금리는 미국 중앙은행인 연방준비제도가 통화정책을 운영할 때 중요한 기준이 되는 금리이다. "
            "기준금리는 예금금리, 대출금리, 채권금리, 기업의 자금조달 비용 등에 영향을 줄 수 있다. "
            "포트폴리오를 이해할 때 기준금리는 채권형 자산, 현금성 자산, 성장주 자산의 특징을 이해하는 데 도움이 된다. "
            "다만 기준금리 하나만으로 특정 자산의 좋고 나쁨이나 미래 수익률을 판단할 수는 없다."
        ),
        source_series_id="FEDFUNDS",
        snapshot=snapshots["FEDFUNDS"],
    ))

    docs.append(make_doc(
        doc_id="macro_funding_cost_001",
        title="기준금리와 자금조달 비용",
        category="거시경제",
        level=3,
        keywords=["기준금리", "자금조달 비용", "대출금리", "기업 비용", "할인율"],
        related_data=["FEDFUNDS"],
        related_portfolio_features=["성장주 자산 비중 높음", "미국 ETF 비중 높음", "채권형 자산 포함"],
        related_quiz_tags=["금리", "기업", "거시경제"],
        content=(
            "기준금리는 기업과 개인이 돈을 빌리는 비용에 영향을 줄 수 있다. "
            "금리가 높아지면 대출이나 회사채 발행을 통한 자금조달 비용이 커질 수 있고, 이는 기업의 투자와 소비 결정에도 영향을 줄 수 있다. "
            "이 개념은 성장주, 채권형 자산, 현금성 자산의 성격을 이해하는 데 도움이 된다. "
            "하지만 기준금리 변화만으로 특정 종목이나 ETF의 방향을 단정해서는 안 된다."
        ),
        source_series_id="FEDFUNDS",
        snapshot=snapshots["FEDFUNDS"],
    ))

    docs.append(make_doc(
        doc_id="macro_dgs10_001",
        title="미국 10년물 국채금리란 무엇인가",
        category="거시경제",
        level=3,
        keywords=["미국 10년물 국채금리", "DGS10", "장기금리", "국채", "채권"],
        related_data=["DGS10"],
        related_portfolio_features=["미국 ETF 비중 높음", "채권형 자산 포함", "장기채 ETF 포함"],
        related_quiz_tags=["채권", "금리", "미국경제"],
        content=(
            "미국 10년물 국채금리는 미국 정부가 발행한 10년 만기 국채의 수익률을 의미한다. "
            "장기금리는 시장이 바라보는 경기, 물가, 통화정책 기대와 연결되어 해석되는 경우가 많다. "
            "포트폴리오를 이해할 때 장기금리는 채권형 자산과 성장주 자산의 가격 변동성을 설명하는 데 자주 등장한다. "
            "단, 이 지표는 시장 환경을 이해하기 위한 참고 자료이지 특정 자산의 투자 판단 기준이 아니다."
        ),
        source_series_id="DGS10",
        snapshot=snapshots["DGS10"],
    ))

    docs.append(make_doc(
        doc_id="macro_bond_price_rate_001",
        title="장기금리와 채권 가격의 관계",
        category="채권",
        level=3,
        keywords=["장기금리", "채권 가격", "국채", "채권형 ETF", "금리"],
        related_data=["DGS10"],
        related_portfolio_features=["채권형 자산 포함", "장기채 ETF 포함", "안정형 포트폴리오"],
        related_quiz_tags=["채권", "금리", "ETF"],
        content=(
            "채권 가격과 시장금리는 일반적으로 반대 방향으로 움직이는 경향이 있다. "
            "시장금리가 상승하면 기존에 낮은 금리로 발행된 채권의 매력이 낮아질 수 있어 채권 가격이 하락할 수 있다. "
            "그래서 채권형 ETF도 예금처럼 고정된 결과를 주는 상품이 아니라 시장금리에 따라 가격이 변할 수 있다. "
            "이 설명은 채권형 자산의 구조를 이해하기 위한 것이며, 특정 채권형 ETF의 좋고 나쁨을 판단하기 위한 것은 아니다."
        ),
        source_series_id="DGS10",
        snapshot=snapshots["DGS10"],
    ))

    docs.append(make_doc(
        doc_id="macro_cpi_001",
        title="CPI란 무엇인가",
        category="거시경제",
        level=2,
        keywords=["CPI", "소비자물가지수", "물가", "인플레이션"],
        related_data=["CPIAUCSL"],
        related_portfolio_features=["현금 비중 높음", "채권형 자산 포함", "미국 ETF 비중 높음"],
        related_quiz_tags=["물가", "인플레이션", "경제지표"],
        content=(
            "CPI는 소비자물가지수를 뜻하며, 소비자가 일상생활에서 구입하는 상품과 서비스의 가격이 평균적으로 어떻게 변했는지를 보여주는 지표이다. "
            "CPI가 상승한다는 것은 생활에 필요한 재화와 서비스의 가격 수준이 올라갔다는 의미로 해석할 수 있다. "
            "포트폴리오를 이해할 때 CPI는 인플레이션, 구매력, 금리 변화와 연결되는 중요한 개념이다. "
            "다만 CPI만으로 특정 자산의 수익률이나 방향을 예측해서는 안 된다."
        ),
        source_series_id="CPIAUCSL",
        snapshot=snapshots["CPIAUCSL"],
    ))

    docs.append(make_doc(
        doc_id="macro_inflation_purchase_power_001",
        title="인플레이션과 구매력",
        category="거시경제",
        level=2,
        keywords=["인플레이션", "구매력", "물가", "CPI", "현금"],
        related_data=["CPIAUCSL"],
        related_portfolio_features=["현금 비중 높음", "안정형 포트폴리오", "채권형 자산 포함"],
        related_quiz_tags=["물가", "인플레이션", "현금"],
        content=(
            "인플레이션은 전반적인 물가 수준이 오르는 현상이다. "
            "물가가 오르면 같은 금액으로 살 수 있는 상품과 서비스의 양이 줄어들 수 있는데, 이를 구매력 하락이라고 설명할 수 있다. "
            "포트폴리오를 이해할 때 인플레이션은 현금 보유, 금리, 채권형 자산, 실질수익률 개념과 연결된다. "
            "이 개념은 자산 구조를 이해하기 위한 것이며 특정 투자 선택을 지시하기 위한 것이 아니다."
        ),
        source_series_id="CPIAUCSL",
        snapshot=snapshots["CPIAUCSL"],
    ))

    docs.append(make_doc(
        doc_id="macro_unrate_001",
        title="실업률이란 무엇인가",
        category="거시경제",
        level=2,
        keywords=["실업률", "UNRATE", "고용", "경기", "노동시장"],
        related_data=["UNRATE"],
        related_portfolio_features=["미국 ETF 비중 높음", "경기민감 자산 포함"],
        related_quiz_tags=["고용", "경기", "미국경제"],
        content=(
            "실업률은 일할 의사와 능력이 있지만 일자리를 구하지 못한 사람이 경제활동인구에서 차지하는 비율을 의미한다. "
            "실업률은 노동시장과 경기 흐름을 이해하는 데 사용되는 대표적인 지표 중 하나이다. "
            "포트폴리오를 이해할 때 실업률은 경기 둔화, 소비 여건, 기업 실적 환경 같은 개념과 연결해서 볼 수 있다. "
            "다만 실업률 하나로 특정 자산의 방향이나 수익률을 판단해서는 안 된다."
        ),
        source_series_id="UNRATE",
        snapshot=snapshots["UNRATE"],
    ))

    docs.append(make_doc(
        doc_id="macro_unemployment_cycle_001",
        title="실업률과 경기 흐름",
        category="거시경제",
        level=3,
        keywords=["실업률", "경기 흐름", "경기침체", "고용", "소비"],
        related_data=["UNRATE"],
        related_portfolio_features=["미국 ETF 비중 높음", "경기민감 자산 포함", "주식형 자산 비중 높음"],
        related_quiz_tags=["경기", "고용", "거시경제"],
        content=(
            "실업률은 경기 흐름을 이해할 때 참고할 수 있는 지표이다. "
            "일반적으로 경기가 약해지면 기업의 고용 여력이 줄어 실업률이 높아질 수 있고, 고용이 안정적이면 소비 여건이 유지되는 데 도움이 될 수 있다. "
            "이 개념은 주식형 자산이나 경기민감 자산이 어떤 경제 환경과 연결되는지 이해하는 데 도움을 준다. "
            "그러나 실업률만 보고 포트폴리오의 적절성이나 특정 자산의 미래 성과를 판단해서는 안 된다."
        ),
        source_series_id="UNRATE",
        snapshot=snapshots["UNRATE"],
    ))

    docs.append(make_doc(
        doc_id="macro_gdp_001",
        title="GDP란 무엇인가",
        category="거시경제",
        level=2,
        keywords=["GDP", "국내총생산", "경제규모", "생산", "소득"],
        related_data=["GDP"],
        related_portfolio_features=["미국 ETF 비중 높음", "주식형 자산 비중 높음", "경기민감 자산 포함"],
        related_quiz_tags=["GDP", "경제성장", "거시경제"],
        content=(
            "GDP는 국내총생산을 뜻하며, 한 나라 안에서 일정 기간 동안 생산된 최종 재화와 서비스의 가치를 합한 지표이다. "
            "GDP는 경제 규모와 경제활동 수준을 이해하는 데 사용된다. "
            "포트폴리오를 이해할 때 GDP는 경기 흐름, 기업 활동, 소비와 투자 환경을 설명하는 기초 개념으로 활용될 수 있다. "
            "단, GDP 수치만으로 특정 자산의 투자 매력이나 미래 수익률을 판단할 수는 없다."
        ),
        source_series_id="GDP",
        snapshot=snapshots["GDP"],
    ))

    docs.append(make_doc(
        doc_id="macro_gdp_growth_001",
        title="GDP와 경제성장률",
        category="거시경제",
        level=3,
        keywords=["GDP", "경제성장률", "경기", "생산", "소비"],
        related_data=["GDP"],
        related_portfolio_features=["미국 ETF 비중 높음", "주식형 자산 비중 높음", "경기민감 자산 포함"],
        related_quiz_tags=["GDP", "경제성장", "경기"],
        content=(
            "경제성장률은 GDP가 이전 기간에 비해 얼마나 늘었는지를 보여주는 지표이다. "
            "경제성장률을 보면 한 나라의 생산과 소비, 투자 활동이 확장되고 있는지 둔화되고 있는지 이해하는 데 도움이 된다. "
            "포트폴리오를 이해할 때 경제성장률은 주식형 자산, 경기민감 자산, 장기 투자 환경을 설명하는 배경 개념으로 활용될 수 있다. "
            "하지만 경제성장률만으로 특정 자산을 평가하거나 수익률을 예측해서는 안 된다."
        ),
        source_series_id="GDP",
        snapshot=snapshots["GDP"],
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
    print(f"\nFRED 기반 RAG 문서 초안 생성 완료: {len(docs)}개")


if __name__ == "__main__":
    main()