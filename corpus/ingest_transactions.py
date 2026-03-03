import pandas as pd
import os

def load_data(filepath: str) -> pd.DataFrame:
    """Load raw transactions."""
    return pd.read_csv(filepath)

def clean_pii(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean personally identifiable information (PII) from the transaction data.
    """
    if "client_sin" in df.columns:
        df["client_sin"] = "***-***-***"
    return df

def write_to_staging(df: pd.DataFrame, engine):
    """
    write cleaned transaction data to the staging table in the warehouse. 
    The target table name is read from an environment variable, defaulting to 'raw_tx_stg' if not set.
    """
    target_table = os.getenv("STAGING_TABLE", "raw_tx_stg")
    df.to_sql(target_table, con=engine, if_exists="replace", index=False)

if __name__ == "__main__":
    from sqlalchemy import create_engine
    engine = create_engine("sqlite:///warehouse.db")
    
    df_raw = load_data("data/raw_transactions.csv")
    df_clean = clean_pii(df_raw)
    write_to_staging(df_clean, engine)