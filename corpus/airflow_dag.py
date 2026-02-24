from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from sqlalchemy import create_engine

DB_URL = "sqlite:///warehouse.db"

default_args = {
    "owner"           : "data-engineering",
    "depends_on_past" : False,
    "retries"         : 2,
    "retry_delay"     : timedelta(minutes=5),
    "email_on_failure": True,
    "email"           : ["data-alerts@wealthsimple.com"],
}

dag = DAG(
    dag_id           = "client_summary_pipeline",
    description      = "End-to-end pipeline: ingest → fees → report",
    schedule_interval= "0 2 * * *",   # daily at 02:00 UTC
    start_date       = datetime(2026, 1, 1),
    catchup          = False,
    default_args     = default_args,
    tags             = ["finance", "reporting", "lineage-demo"],
)

def run_ingest():
    from corpus.ingest_transactions import (
        load_raw_transactions, clean_transactions, write_transactions
    )
    engine = create_engine(DB_URL)
    raw    = load_raw_transactions("data/raw_transactions.csv")
    clean  = clean_transactions(raw)
    write_transactions(clean, engine)

def run_compute_fees():
    from corpus.compute_fees import (
        load_transactions, load_accounts, compute_fees, write_fees
    )
    engine       = create_engine(DB_URL)
    transactions = load_transactions(engine)
    accounts     = load_accounts(engine)
    fees         = compute_fees(transactions, accounts)
    write_fees(fees, engine)

def run_generate_report():
    """Execute the client_summary SQL report against the warehouse."""
    import sqlite3, pathlib
    sql  = pathlib.Path("corpus/generate_report.sql").read_text()
    conn = sqlite3.connect("warehouse.db")
    conn.executescript(sql)
    conn.commit()
    conn.close()

ingest_task = PythonOperator(
    task_id         = "ingest_transactions",
    python_callable = run_ingest,
    dag             = dag,
)

fees_task = PythonOperator(
    task_id         = "compute_fees",
    python_callable = run_compute_fees,
    dag             = dag,
)

report_task = PythonOperator(
    task_id         = "generate_report",
    python_callable = run_generate_report,
    dag             = dag,
)

# DAG dependency chain
ingest_task >> fees_task >> report_task
