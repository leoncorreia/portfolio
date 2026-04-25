from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Iterable

import pandas as pd

from stock_pipeline.config import DatabaseConfig, get_database_config, get_symbols_from_env

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {"timestamp", "close", "volume"}


def stock_prices_insert_query() -> str:
    return """
        INSERT INTO stock_prices (symbol, timestamp, price, volume, ingested_at)
        VALUES %s
        ON CONFLICT (symbol, timestamp) DO NOTHING;
    """


def fetch_symbol_history(symbol: str) -> pd.DataFrame:
    import yfinance as yf

    logger.info("Fetching yfinance history for symbol=%s", symbol)
    history = yf.Ticker(symbol).history(period="1d", interval="1m", auto_adjust=False, actions=False)
    if history.empty:
        logger.warning("No data returned by yfinance for symbol=%s", symbol)
        return pd.DataFrame()
    return history.reset_index()


def transform_history(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["symbol", "timestamp", "price", "volume"])

    transformed = df.copy()
    transformed.columns = [column.strip().lower() for column in transformed.columns]

    if "datetime" in transformed.columns and "timestamp" not in transformed.columns:
        transformed = transformed.rename(columns={"datetime": "timestamp"})

    missing_columns = REQUIRED_COLUMNS.difference(transformed.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns for symbol={symbol}: {sorted(missing_columns)}")

    transformed["timestamp"] = pd.to_datetime(transformed["timestamp"], errors="coerce", utc=True)
    transformed["price"] = pd.to_numeric(transformed["close"], errors="coerce")
    transformed["volume"] = pd.to_numeric(transformed["volume"], errors="coerce")
    transformed["symbol"] = symbol.upper()

    transformed = transformed.dropna(subset=["symbol", "timestamp", "price", "volume"]).copy()
    transformed["timestamp"] = transformed["timestamp"].dt.tz_convert(None)
    transformed["volume"] = transformed["volume"].astype("int64")
    transformed = transformed[["symbol", "timestamp", "price", "volume"]]
    transformed = transformed.drop_duplicates(subset=["symbol", "timestamp"], keep="last")

    return transformed.sort_values("timestamp")


def insert_stock_prices(rows: pd.DataFrame, db_config: DatabaseConfig) -> int:
    import psycopg2
    from psycopg2.extras import execute_values

    if rows.empty:
        logger.info("No rows to insert after transformations.")
        return 0

    query = stock_prices_insert_query()

    payload = [
        (
            row.symbol,
            row.timestamp.to_pydatetime() if hasattr(row.timestamp, "to_pydatetime") else row.timestamp,
            float(row.price),
            int(row.volume),
            datetime.now(timezone.utc),
        )
        for row in rows.itertuples(index=False)
    ]

    with psycopg2.connect(
        host=db_config.host,
        port=db_config.port,
        dbname=db_config.dbname,
        user=db_config.user,
        password=db_config.password,
    ) as conn:
        with conn.cursor() as cursor:
            execute_values(cursor, query, payload, page_size=500)
            inserted = cursor.rowcount if cursor.rowcount and cursor.rowcount > 0 else 0
        conn.commit()

    logger.info("Insert attempted for %s rows; inserted=%s", len(payload), inserted)
    return inserted


def run_extract_load(symbols: Iterable[str], db_config: DatabaseConfig | None = None) -> int:
    config = db_config or get_database_config()
    total_inserted = 0

    for symbol in symbols:
        history = fetch_symbol_history(symbol)
        cleaned = transform_history(history, symbol)
        inserted = insert_stock_prices(cleaned, config)
        total_inserted += inserted
        logger.info("Completed extract/load for symbol=%s inserted=%s", symbol, inserted)

    if total_inserted == 0:
        logger.warning("Pipeline completed with zero inserts for symbols=%s", list(symbols))

    return total_inserted


def run_extract_load_from_env(symbols: list[str] | None = None) -> int:
    selected_symbols = symbols or get_symbols_from_env()
    if not selected_symbols:
        raise ValueError("No stock symbols configured. Set STOCK_SYMBOLS or Airflow Variable stock_symbols.")
    logger.info("Starting extract/load for symbols=%s", selected_symbols)
    return run_extract_load(selected_symbols)

