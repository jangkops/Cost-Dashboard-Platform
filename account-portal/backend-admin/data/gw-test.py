import json, sys, boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import requests

API = "https://5l764dh7y9.execute-api.us-west-2.amazonaws.com/v1"
SEP = "=" * 60

def sigv4_post(path, body_dict):
    url = API + path
    body = json.dumps(body_dict)
    session = boto3.Session()
    creds = session.get_credentials().get_frozen_credentials()
    req = AWSRequest(method="POST", url=url, data=body, headers={"Content-Type": "application/json"})
    SigV4Auth(creds, "execute-api", "us-west-2").add_auth(req)
    resp = requests.post(url, data=body, headers=dict(req.headers))
    return resp.status_code, resp.json()

def step(n, desc):
    print("\n" + SEP)
    print("STEP %d: %s" % (n, desc))
    print(SEP)

step(0, "Identity")
sts = boto3.client("sts")
id_resp = sts.get_caller_identity()
print("ARN: " + id_resp["Arn"])
print("Account: " + id_resp["Account"])

step(1, "Inference")
code, data = sigv4_post("/converse", {
    "modelId": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "messages": [{"role": "user", "content": [{"text": "Say hello in 3 words"}]}]
})
print("HTTP %d" % code)
print(json.dumps(data, indent=2, ensure_ascii=False)[:800])

if code == 200:
    print("\nremaining_quota: %s" % data.get("remaining_quota", {}))
    print("estimated_cost_krw: %s" % data.get("estimated_cost_krw"))
elif code == 429:
    print("\nband: %s" % data.get("band", {}))
    print("increase_request: %s" % data.get("increase_request", {}))
    print("message: %s" % data.get("message", ""))

print("\n" + SEP)
print("Done. Copy output above to Kiro.")
print(SEP)
