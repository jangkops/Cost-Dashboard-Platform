from flask import Blueprint, request, jsonify
import boto3

instances_bp = Blueprint("instances", __name__)

@instances_bp.route("/api/instances", methods=["POST"])
def get_instances():
    """선택한 리전의 running 상태 EC2 인스턴스 목록 반환 (compute만 제외)"""
    data = request.json
    region = data.get("region")

    if not region:
        return jsonify({"error": "region is required"}), 400

    ec2 = boto3.client("ec2", region_name=region)
    res = ec2.describe_instances(
        Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
    )

    instance_list = []

    for reservation in res.get("Reservations", []):
        for inst in reservation.get("Instances", []):
            name = next(
                (tag["Value"] for tag in inst.get("Tags", []) if tag["Key"] == "Name"),
                inst.get("InstanceId")
            )
            
            # compute로 시작하는 인스턴스만 제외
            if not name.lower().startswith("compute"):
                instance_list.append({
                    "instanceId": inst.get("InstanceId"),
                    "state": inst.get("State", {}).get("Name", "unknown"),
                    "name": name
                })

    return jsonify({"instances": instance_list})
