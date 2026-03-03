import pandas as pd
import os

def load_staging_data(engine) -> pd.DataFrame:
    """
    Load raw transaction data from the staging table.
    """
    source_table = os.getenv("STAGING_TABLE", "raw_tx_stg")
    return pd.read_sql(f"SELECT * FROM {source_table}", con=engine)

def load_accounts(engine) -> pd.DataFrame:
    """Load static account data."""
    return pd.read_sql("SELECT * FROM accounts", con=engine)

def compute_fees(df_tx: pd.DataFrame, df_acc: pd.DataFrame) -> pd.DataFrame:
    """Join transactions with accounts and compute flat fee."""
    df_merged = df_tx.merge(df_acc, on="client_id", how="left")
    df_merged["fee_amount"] = df_merged["amount"] * 0.015
    return df_merged

def write_fees(df: pd.DataFrame, engine):
    """Write computed fees to the warehouse."""
    df.to_sql("fees", con=engine, if_exists="replace", index=False)

if __name__ == "__main__":
    from sqlalchemy import create_engine
    engine = create_engine("sqlite:///warehouse.db")
    
    df_stg_tx = load_staging_data(engine)
    df_accounts = load_accounts(engine)
    
    df_fees = compute_fees(df_stg_tx, df_accounts)
    write_fees(df_fees, engine)