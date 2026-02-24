import pandas as pd
import sqlalchemy

FEE_RATE_STANDARD = 0.015       # 1.5% for standard accounts
FEE_RATE_PREMIUM  = 0.008       # 0.8% for premium accounts
MIN_FEE_CAD       = 1.50        # minimum fee floor in CAD

def load_transactions(engine: sqlalchemy.engine.Engine) -> pd.DataFrame:
    """Read cleaned transactions from warehouse."""
    return pd.read_sql("SELECT * FROM transactions", con=engine)

def load_accounts(engine: sqlalchemy.engine.Engine) -> pd.DataFrame:
    """Read account tier data to determine fee rate."""
    return pd.read_sql("SELECT client_id, account_tier FROM accounts", con=engine)

def compute_fees(transactions: pd.DataFrame, accounts: pd.DataFrame) -> pd.DataFrame:
    """
    Join transactions with account tiers and compute fee per transaction.
    - Premium accounts get discounted fee rate
    - All fees floored at MIN_FEE_CAD
    - fee_amount = amount_cad * rate, floored at minimum
    """
    df = transactions.merge(accounts, on="client_id", how="left")
    df["fee_rate"] = df["account_tier"].apply(
        lambda t: FEE_RATE_PREMIUM if t == "premium" else FEE_RATE_STANDARD
    )
    df["fee_amount"] = (df["amount_cad"] * df["fee_rate"]).clip(lower=MIN_FEE_CAD)
    df["net_amount"] = df["amount_cad"] - df["fee_amount"]
    return df[["transaction_id", "client_id", "amount_cad",
               "fee_rate", "fee_amount", "net_amount", "settlement_date"]]

def write_fees(df: pd.DataFrame, engine: sqlalchemy.engine.Engine):
    """Write computed fees to the fees table."""
    df.to_sql("fees", con=engine, if_exists="replace", index=False)

if __name__ == "__main__":
    from sqlalchemy import create_engine
    engine = create_engine("sqlite:///warehouse.db")
    transactions = load_transactions(engine)
    accounts     = load_accounts(engine)
    fees         = compute_fees(transactions, accounts)
    write_fees(fees, engine)
    print(f"Computed fees for {len(fees)} transactions")
