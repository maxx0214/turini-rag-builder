from pathlib import Path

import pandas as pd
import yfinance as yf


MAPPING_PATH = Path("data/processed/popular_asset_mapping.csv")
OUTPUT_DIR = Path("data/processed")
OUTPUT_PATH = OUTPUT_DIR / "yfinance_prices.csv"


def load_tickers():
    if not MAPPING_PATH.exists():
        raise FileNotFoundError(
            f"{MAPPING_PATH} 파일이 없습니다. 먼저 popular_asset_mapping.csv를 만들어주세요."
        )

    if MAPPING_PATH.stat().st_size == 0:
        raise ValueError(
            f"{MAPPING_PATH} 파일이 비어 있습니다. popular_asset_mapping.csv 내용을 먼저 넣어주세요."
        )

    mapping_df = pd.read_csv(MAPPING_PATH)

    if "ticker" not in mapping_df.columns:
        raise ValueError("popular_asset_mapping.csv에 ticker 컬럼이 없습니다.")

    tickers = (
        mapping_df["ticker"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )

    if not tickers:
        raise ValueError("수집할 ticker가 없습니다.")

    return tickers


def normalize_ticker_df(ticker_df, ticker):
    """
    yfinance에서 받은 데이터프레임의 날짜 컬럼을 date로 통일한다.
    현재 문제는 reset_index() 후 날짜 컬럼이 index로 저장되는 경우였음.
    """

    ticker_df = ticker_df.reset_index()

    # 날짜 컬럼 후보들
    possible_date_cols = ["Date", "Datetime", "date", "datetime", "index", "Price"]

    date_col = None
    for col in possible_date_cols:
        if col in ticker_df.columns:
            date_col = col
            break

    if date_col is None:
        raise ValueError(
            f"{ticker} 데이터에서 날짜 컬럼을 찾을 수 없습니다. 현재 컬럼: {ticker_df.columns.tolist()}"
        )

    ticker_df = ticker_df.rename(columns={date_col: "date"})

    # 가격 컬럼 확인
    if "Close" not in ticker_df.columns:
        raise ValueError(
            f"{ticker} 데이터에 Close 컬럼이 없습니다. 현재 컬럼: {ticker_df.columns.tolist()}"
        )

    # 필요한 컬럼만 남기기
    keep_cols = ["date", "Open", "High", "Low", "Close", "Volume"]

    existing_cols = [col for col in keep_cols if col in ticker_df.columns]
    ticker_df = ticker_df[existing_cols].copy()

    ticker_df["ticker"] = ticker

    ticker_df["date"] = pd.to_datetime(ticker_df["date"], errors="coerce")
    ticker_df["Close"] = pd.to_numeric(ticker_df["Close"], errors="coerce")

    ticker_df = ticker_df.dropna(subset=["date", "Close"])

    return ticker_df


def collect_yfinance_data(tickers):
    print("yfinance 데이터 수집 시작")
    print(f"수집 티커 수: {len(tickers)}")
    print(tickers)

    data = yf.download(
        tickers,
        start="2015-01-01",
        auto_adjust=True,
        group_by="ticker",
        progress=True,
        threads=True,
    )

    rows = []

    for ticker in tickers:
        try:
            # 여러 티커 다운로드 시 data[ticker] 형태로 접근
            raw_ticker_df = data[ticker]

            if raw_ticker_df.empty:
                print(f"[경고] {ticker} 데이터가 비어 있습니다.")
                continue

            ticker_df = normalize_ticker_df(raw_ticker_df, ticker)

        except Exception as e:
            print(f"[경고] {ticker} 데이터 처리 실패: {e}")
            continue

        rows.append(ticker_df)

        print(f"수집 완료: {ticker}, rows={len(ticker_df)}")

    if not rows:
        raise ValueError("수집된 yfinance 데이터가 없습니다.")

    result = pd.concat(rows, ignore_index=True)

    # 컬럼 순서 정리
    preferred_cols = ["date", "Open", "High", "Low", "Close", "Volume", "ticker"]
    existing_cols = [col for col in preferred_cols if col in result.columns]
    result = result[existing_cols]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    result.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    print("\nyfinance 가격 데이터 저장 완료")
    print(f"저장 위치: {OUTPUT_PATH}")
    print(f"데이터 크기: {result.shape}")
    print(f"컬럼: {result.columns.tolist()}")


def main():
    tickers = load_tickers()
    collect_yfinance_data(tickers)


if __name__ == "__main__":
    main()