-- ============================================================
-- client_summary report
-- Source tables : fees, accounts
-- Target table  : client_summary
-- Purpose       : Monthly client-level summary for compliance
--                 reporting and client statements.
-- Owner         : Data & Analytics team
-- ============================================================

INSERT INTO client_summary (
    client_id,
    full_name,
    account_tier,
    total_transactions,
    total_amount_cad,
    total_fees,
    net_deposits,
    report_month
)
SELECT
    a.client_id,
    a.full_name,
    a.account_tier,
    COUNT(f.transaction_id)          AS total_transactions,
    SUM(f.amount_cad)                AS total_amount_cad,
    SUM(f.fee_amount)                AS total_fees,
    SUM(f.net_amount)                AS net_deposits,
    DATE_TRUNC('month', f.settlement_date) AS report_month
FROM fees f
JOIN accounts a
    ON f.client_id = a.client_id
WHERE
    f.settlement_date >= DATE_TRUNC('month', CURRENT_DATE)
    AND f.settlement_date <  DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
GROUP BY
    a.client_id,
    a.full_name,
    a.account_tier,
    DATE_TRUNC('month', f.settlement_date)
ORDER BY
    net_deposits DESC;
