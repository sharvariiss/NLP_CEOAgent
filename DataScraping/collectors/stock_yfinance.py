"""
Stock Price Data collector — yfinance.
Airbus SE trades on Euronext Paris under ticker AIR.PA.
"""
import yfinance as yf
from .base import make_document, now_iso, DATA_DIR

TICKER = "AIR.PA"


def collect(period="1y"):
    docs = []
    ticker = yf.Ticker(TICKER)

    # 1. Price history -> one summary document + a raw CSV for the dashboard
    hist = ticker.history(period=period)
    if not hist.empty:
        summary = (
            f"Airbus ({TICKER}) price history over the last {period}: "
            f"open {hist['Open'].iloc[0]:.2f}, latest close {hist['Close'].iloc[-1]:.2f}, "
            f"period high {hist['High'].max():.2f}, period low {hist['Low'].min():.2f}."
        )
        docs.append(make_document(
            source_name="Yahoo Finance (yfinance)",
            source_category="stock",
            title=f"{TICKER} price history ({period})",
            url=f"https://finance.yahoo.com/quote/{TICKER}",
            published_date=now_iso(),
            content=summary,
            metadata={"rows": len(hist), "csv_path": "data/raw/airbus_price_history.csv"},
        ))
        hist.to_csv(DATA_DIR / "airbus_price_history.csv")
    else:
        print(f"  [warn] yfinance returned no price history for {TICKER}")

    # 2. Recent news headlines tied to the ticker (bonus signal — yfinance
    #    only gives headlines/links, not full body text)
    try:
        for item in (ticker.news or [])[:50]:
            docs.append(make_document(
                source_name="Yahoo Finance News",
                source_category="stock",
                title=item.get("title", ""),
                url=item.get("link", ""),
                published_date=item.get("providerPublishTime"),
                content=item.get("title", ""),
                metadata={"publisher": item.get("publisher")},
            ))
    except Exception as e:
        print(f"  [warn] yfinance .news fetch failed: {e}")

    return docs
