import sqlite3
import json

conn = sqlite3.connect('revenue_recovery.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 1. Amount distribution
cur.execute("SELECT amount FROM risk_events WHERE split='holdout'")
amounts = [row['amount'] for row in cur.fetchall()]
above_25k = sum(1 for a in amounts if a > 2500000)
print(f"Holdout amounts: {len(amounts)} cases. {above_25k} are > 25k INR (2,500,000 paise).")
if amounts:
    print(f"Min: {min(amounts)}, Max: {max(amounts)}")

# 2 & 3. Check pre-existing state
cur.execute("SELECT id FROM risk_events WHERE split='holdout'")
holdout_ids = [row['id'] for row in cur.fetchall()]

placeholders = ','.join(['?']*len(holdout_ids))
cur.execute(f"SELECT COUNT(*) as count FROM promise_to_pays WHERE case_id IN ({placeholders})", holdout_ids)
ptp_count = cur.fetchone()['count']
print(f"PTPs on holdout cases in DB: {ptp_count}")

cur.execute(f"SELECT case_id, COUNT(*) as count FROM audit_log_entries WHERE case_id IN ({placeholders}) AND action='execute' GROUP BY case_id", holdout_ids)
execute_counts = cur.fetchall()
print(f"Cases with executes in audit_log_entries: {len(execute_counts)}")
for row in execute_counts[:3]:
    print(f"  {row['case_id']} has {row['count']} executes")

print("Checking recent guardrail results for holdout...")
cur.execute(f"SELECT event_id, rule_name, reason FROM guardrail_results WHERE passed=0 AND event_id IN ({placeholders}) ORDER BY checked_at DESC LIMIT 10", holdout_ids)
blocks = cur.fetchall()
for b in blocks:
    print(dict(b))
