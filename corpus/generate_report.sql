-- Target table: client_summary (Final Sink)
-- Purpose: End-of-month client statements

INSERT INTO client_summary (client_id, total_transactions, total_fees)
SELECT 
    f.client_id, 
    COUNT(f.transaction_id) as total_transactions,
    SUM(f.fee_amount) as total_fees
FROM fees f
JOIN accounts a ON f.client_id = a.client_id
GROUP BY f.client_id;