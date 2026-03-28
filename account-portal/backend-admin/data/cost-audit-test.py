#!/usr/bin/env python3
"""Bedrock Gateway Cost Accuracy Audit — Multi-model + Concurrent Test
Run as cgjang on r7: python3 /tmp/cost-audit-test.py
"""
import json, boto3, time, uuid, sys, concurrent.futures
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import urllib.request

API = "https://5l764dh7y9.execute-api.us-west-2.amazonaws.com/v1"
REGION = "us-west-2"
FX = 1450

# AWS official on-demand pricing (us-west-2, per 1K tokens, USD)
OFFICIAL = {
    "us.anthropic.claude-haiku-4-5-20251001-v1:0": (0.001, 0.005),
    "us.amazon.nova-micro-v1:0": (0.000035, 0.00014),
}

session = boto3.Session(region_name=REGION)

def call(model_id, text, rid=None):
    creds = session.get_credentials().get_frozen_credentials()
    rid = rid or f"audit-{uuid.uuid4().hex[:12]}"
    body = json.dumps({"modelId": model_id,
                        "messages": [{"role":"user","content":[{"text":text}]}]})
    r = AWSRequest(method="POST", url=f"{API}/converse", data=body,
                   headers={"Content-Type":"application/json","X-Request-Id":rid})
    SigV4Auth(creds, "execute-api", REGION).add_auth(r)
    h = urllib.request.Request(f"{API}/converse", data=body.encode(),
                               headers=dict(r.headers), method="POST")
    try:
        resp = urllib.request.urlopen(h, timeout=30)
        return resp.getcode(), json.loads(resp.read().decode()), rid
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode()), rid

print("=== SEQUENTIAL CALLS ===")
for mid, (ip, op) in OFFICIAL.items():
    code, data, rid = call(mid, "Say hello. One word only.")
    if code == 200:
        u = data.get("usage", {})
        cost = data.get("estimated_cost_krw", 0)
        inp, out = u.get("inputTokens",0), u.get("outputTokens",0)
        official = (inp * ip / 1000 + out * op / 1000) * FX
        diff = abs(cost - official)
        print(f"  {mid}: in={inp} out={out} gw_cost={cost:.6f} official={official:.6f} diff={diff:.6f} {'PASS' if diff<0.001 else 'FAIL'}")
    else:
        print(f"  {mid}: HTTP {code} — {data.get('denial_reason','')}")

print("\n=== CONCURRENT 5x HAIKU ===")
def do_call(i):
    rid = f"audit-par-{i}-{uuid.uuid4().hex[:8]}"
    return call("us.anthropic.claude-haiku-4-5-20251001-v1:0", f"Count {i}.", rid)

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
    futs = [ex.submit(do_call, i) for i in range(5)]
    for f in concurrent.futures.as_completed(futs):
        code, data, rid = f.result()
        if code == 200:
            u = data.get("usage",{})
            print(f"  {rid}: in={u.get('inputTokens',0)} out={u.get('outputTokens',0)} cost={data.get('estimated_cost_krw',0):.6f}")
        else:
            print(f"  {rid}: HTTP {code}")

print("\nDONE")
