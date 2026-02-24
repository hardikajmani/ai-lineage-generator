import pandas as pd
import sqlalchemy

def load_raw_transactions(filepath: str) -> pd.DataFrame:
    """Load raw transaction CSV from upstream data drop."""
    df = pd.read_csv(filepath)
    return df

def clean_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and normalize raw transactions.
    - Drop rows with null client_id or amount
    - Filter out cancelled transactions
    - Normalize currency to CAD
    """
    df = df.dropna(subset=["client_id", "amount"])
    df = df[df["status"] != "cancelled"]
    df["amount_cad"] = df["amount"] * df["fx_rate"]
    df["settlement_date"] = pd.to_datetime(df["settlement_date"])
    df = df.rename(columns={"tx_id": "transaction_id"})
    return df

def write_transactions(df: pd.DataFrame, engine: sqlalchemy.engine.Engine):
    """Write cleaned transactions to the transactions table."""
    df.to_sql("transactions", con=engine, if_exists="replace", index=False)

if __name__ == "__main__":
    from sqlalchemy import create_engine
    engine = create_engine("sqlite:///warehouse.db")
    raw = load_raw_transactions("data/raw_transactions.csv")
    clean = clean_transactions(raw)
    write_transactions(clean, engine)
    print(f"Ingested {len(clean)} transactions into warehouse.db")
