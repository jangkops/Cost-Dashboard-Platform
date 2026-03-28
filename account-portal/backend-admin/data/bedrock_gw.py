"""
bedrock_gw — Bedrock Gateway Python 클라이언트

사용법:
    from bedrock_gw import converse
    response = converse("us.anthropic.claude-haiku-4-5-20251001-v1:0", "안녕하세요")

한도 초과 시 자동으로 증액 요청 여부를 묻습니다.
"""
import json, sys, os, boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import requests as _req

API = os.environ.get(
    "BEDROCK_GW_API",
    "https://5l764dh7y9.execute-api.us-west-2.amazonaws.com/v1",
)
_REGION = "us-west-2"
_SERVICE = "execute-api"


def _sigv4_post(path, body_dict):
    url = API + path
    body = json.dumps(body_dict)
    session = boto3.Session()
    creds = session.get_credentials().get_frozen_credentials()
    req = AWSRequest(method="POST", url=url, data=body,
                     headers={"Content-Type": "application/json"})
    SigV4Auth(creds, _SERVICE, _REGION).add_auth(req)
    resp = _req.post(url, data=body, headers=dict(req.headers))
    return resp.status_code, resp.json()


def _is_interactive():
    return hasattr(sys.stdin, "isatty") and sys.stdin.isatty()


def _handle_quota_exceeded(data):
    inc = data.get("increase_request", {})
    msg = data.get("message", "")
    print("\n[Bedrock Gateway] " + msg)

    if not inc.get("can_request"):
        if inc.get("has_pending"):
            print("  -> 증액 요청이 이미 접수되어 관리자 승인 대기 중입니다.")
        else:
            print("  -> 월간 최대 한도에 도달하여 추가 증액이 불가합니다.")
        return None

    if not _is_interactive():
        print("  -> 비대화형 환경입니다. 증액 요청을 하려면:")
        print("     from bedrock_gw import request_increase")
        print("     request_increase('사유')")
        return None

    print("  현재 한도: KRW %s" % "{:,}".format(inc.get("new_limit_if_approved_krw", 0) - 500000))
    print("  증액분: KRW 500,000")
    print("  승인 시 새 한도: KRW %s" % "{:,}".format(inc.get("new_limit_if_approved_krw", 0)))
    try:
        answer = input("  한도 증액을 요청하시겠습니까? (y/n): ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n  요청이 취소되었습니다.")
        return None

    if answer != "y":
        print("  요청이 취소되었습니다.")
        return None

    return request_increase("한도 소진으로 증액 요청")


def request_increase(reason="한도 소진으로 증액 요청"):
    """명시적으로 한도 증액을 요청합니다."""
    code, data = _sigv4_post("/approval/request", {
        "reason": reason,
        "requested_increment_krw": 500000,
    })
    if code == 201 and data.get("decision") == "ACCEPTED":
        aid = data.get("approval_id", "")
        print("\n  [OK] 한도 증액 요청이 접수되었습니다.")
        print("  승인 요청 ID: %s" % aid)
        print("  관리자 승인 후 자동으로 한도가 적용됩니다.")
        return data
    else:
        reason_msg = data.get("denial_reason", str(data))
        print("\n  [FAIL] 요청 실패: %s" % reason_msg)
        return data


def converse(model_id, text, **kwargs):
    """Gateway를 통해 Bedrock Converse API를 호출합니다.

    Args:
        model_id: 모델 ID (예: "us.anthropic.claude-haiku-4-5-20251001-v1:0")
        text: 사용자 메시지 텍스트
        **kwargs: messages, system, inferenceConfig 등 추가 파라미터

    Returns:
        Gateway 응답 dict (decision=ALLOW 시 output, usage, remaining_quota 포함)
    """
    body = {"modelId": model_id}
    if "messages" in kwargs:
        body["messages"] = kwargs["messages"]
    else:
        body["messages"] = [{"role": "user", "content": [{"text": text}]}]
    if "system" in kwargs:
        body["system"] = kwargs["system"]
    if "inferenceConfig" in kwargs:
        body["inferenceConfig"] = kwargs["inferenceConfig"]

    code, data = _sigv4_post("/converse", body)

    if code == 200:
        # Check near-limit warning from remaining quota
        remaining = data.get("remaining_quota", {}).get("cost_krw", float("inf"))
        effective = remaining + data.get("estimated_cost_krw", 0) + \
                    (data.get("usage", {}).get("inputTokens", 0) * 0.001)  # rough
        if remaining < 50000 and _is_interactive():  # < 50K KRW remaining
            print("\n  [Bedrock Gateway] 잔여 한도가 KRW {:,.0f} 입니다.".format(remaining),
                  file=sys.stderr)
        return data
    elif code == 429:
        result = _handle_quota_exceeded(data)
        if result and result.get("decision") == "ACCEPTED" and _is_interactive():
            print("  승인 요청이 접수되었습니다. 관리자 승인 후 재시도하세요.")
        return data
    else:
        print("[Bedrock Gateway] HTTP %d: %s" % (code, data.get("denial_reason", "")))
        return data
