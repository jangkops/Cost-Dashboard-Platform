#!/usr/bin/env python3
"""Bedrock Gateway — Ledger vs Aggregate Reconciliation Script

Usage:
    python3 reconcile-usage.py [--month YYYY-MM] [--profile virginia-sso]

Compares ledger ALLOW row sums with monthly-usage aggregate values.
Reports drift with cause classification.
"""
import boto3, argparse, sys
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from collections import defaultdict

TOLERANCE_KRW = 0.01  # 허용 오차 (KRW)

def main():
    parser = argparse.ArgumentParser(description='Ledger vs Aggregate Reconciliation')
    parser.add_argument('--month', default=None, help='YYYY-MM (default: current KST month)')
    parser.add_argument('--profile', default='virginia-sso')
    parser.add_argument('--region', default='us-west-2')
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    dynamodb = session.resource('dynamodb')

    KST = timezone(timedelta(hours=9))
    month = args.month or datetime.now(KST).strftime('%Y-%m')
    print(f"Reconciliation for month: {month}")

    # Scan all ledger ALLOW rows for this month
    lt = dynamodb.Table('bedrock-gw-dev-us-west-2-request-ledger')
    all_ledger = []
    resp = lt.scan()
    all_ledger.extend(resp.get('Items', []))
    while 'LastEvaluatedKey' in resp:
        resp = lt.scan(ExclusiveStartKey=resp['LastEvaluatedKey'])
        all_ledger.extend(resp.get('Items', []))

    # Filter to month + ALLOW
    month_allow = [r for r in all_ledger
                   if r.get('decision') == 'ALLOW' and month in r.get('timestamp', '')]

    # Sum by principal+model
    sums = defaultdict(lambda: {'cost': Decimal('0'), 'in': 0, 'out': 0, 'count': 0})
    for r in month_allow:
        key = f"{r.get('principal_id', '')}|{r.get('model_id', '')}"
        sums[key]['cost'] += Decimal(str(r.get('estimated_cost_krw', 0)))
        sums[key]['in'] += int(r.get('input_tokens', 0))
        sums[key]['out'] += int(r.get('output_tokens', 0))
        sums[key]['count'] += 1

    # Scan monthly-usage
    ut = dynamodb.Table('bedrock-gw-dev-us-west-2-monthly-usage')
    usage_resp = ut.scan()
    all_usage = [i for i in usage_resp.get('Items', []) if month in i.get('principal_id_month', '')]

    # Compare
    drift_count = 0
    match_count = 0
    for key, s in sorted(sums.items()):
        pid, mid = key.split('|')
        month_pk = f"{pid}#{month}"
        matching = [u for u in all_usage if u.get('principal_id_month') == month_pk and u.get('model_id') == mid]
        if not matching:
            print(f"  DRIFT: {pid.split('#')[-1]} | {mid} — ledger exists but NO aggregate row")
            drift_count += 1
            continue
        mu = matching[0]
        mu_cost = float(mu.get('cost_krw', 0))
        cost_diff = mu_cost - float(s['cost'])
        in_diff = int(mu.get('input_tokens', 0)) - s['in']
        out_diff = int(mu.get('output_tokens', 0)) - s['out']
        if abs(cost_diff) > TOLERANCE_KRW or in_diff != 0 or out_diff != 0:
            user = pid.split('#')[-1]
            print(f"  DRIFT: {user} | {mid}")
            print(f"    Ledger:    cost={float(s['cost']):.6f} in={s['in']} out={s['out']} ({s['count']} rows)")
            print(f"    Aggregate: cost={mu_cost:.6f} in={int(mu.get('input_tokens',0))} out={int(mu.get('output_tokens',0))}")
            print(f"    Diff:      cost={cost_diff:.6f} in={in_diff} out={out_diff}")
            drift_count += 1
        else:
            match_count += 1

    # Check for aggregate rows with no ledger
    for u in all_usage:
        pk = u.get('principal_id_month', '')
        mid = u.get('model_id', '')
        pid = '#'.join(pk.split('#')[:-1])
        key = f"{pid}|{mid}"
        if key not in sums and float(u.get('cost_krw', 0)) > 0:
            print(f"  DRIFT: aggregate exists but NO ledger rows — {pid.split('#')[-1]} | {mid}")
            drift_count += 1

    print(f"\nResult: {match_count} MATCH, {drift_count} DRIFT (tolerance={TOLERANCE_KRW} KRW)")
    sys.exit(1 if drift_count > 0 else 0)

if __name__ == '__main__':
    main()
