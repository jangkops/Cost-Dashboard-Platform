import json
import time
import os
import subprocess
import psutil
import boto3
from datetime import datetime

def get_instance_id():
    try:
        response = subprocess.run(["curl", "-s", "http://169.254.169.254/latest/meta-data/instance-id"], 
                                capture_output=True, text=True, timeout=5)
        return response.stdout.strip()
    except:
        return "unknown"

def get_mapping_info(instance_id):
    try:
        s3 = boto3.client("s3")
        response = s3.get_object(Bucket="mogam-or-cur-stg", Key="config/mapping.json")
        mapping = json.loads(response["Body"].read().decode("utf-8"))
        
        instance_info = mapping.get("instance_mapping", {}).get(instance_id, {})
        project_code = instance_info.get("project_code", "unknown")
        project_info = mapping.get("project_mapping", {}).get(project_code, {})
        
        infra_type = instance_info.get("infrastructure_type", "unknown")
        
        return {
            "username": instance_info.get("username", "unknown"),
            "project_code": project_code,
            "project_name": project_info.get("project_name", "unknown"),
            "cost_center": project_info.get("cost_center", "unknown"),
            "instance_type": instance_info.get("instance_type", "unknown"),
            "infrastructure_type": infra_type,
            "parent_cluster": instance_info.get("parent_cluster"),
            "queue_name": instance_info.get("queue_name"),
            "budget_limit": project_info.get("budget_limit", 0)
        }
    except Exception as e:
        return {
            "username": "unknown",
            "project_code": "unknown", 
            "project_name": "unknown",
            "cost_center": "unknown",
            "instance_type": "unknown",
            "infrastructure_type": "unknown",
            "parent_cluster": None,
            "queue_name": None,
            "budget_limit": 0
        }

def get_gpu_occupancy():
    try:
        result = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            total_used = sum(int(line.split(",")[0]) for line in lines)
            total_memory = sum(int(line.split(",")[1]) for line in lines)
            return round((total_used / total_memory) * 100, 2) if total_memory > 0 else 0
    except:
        pass
    return 0

def get_gpu_count():
    try:
        result = subprocess.run(["nvidia-smi", "-L"], capture_output=True, text=True)
        return len(result.stdout.strip().split("\n")) if result.returncode == 0 else 0
    except:
        return 0

def get_slurm_job_id():
    try:
        if "SLURM_JOB_ID" in os.environ:
            return os.environ["SLURM_JOB_ID"]
        for proc in psutil.process_iter(["pid", "environ"]):
            try:
                if proc.info["environ"] and "SLURM_JOB_ID" in proc.info["environ"]:
                    return proc.info["environ"]["SLURM_JOB_ID"]
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except:
        pass
    return None

def collect_and_upload():
    s3 = boto3.client("s3")
    instance_id = get_instance_id()
    
    while True:
        try:
            now = datetime.utcnow()
            mapping_info = get_mapping_info(instance_id)
            
            metrics = {
                "timestamp": now.isoformat(),
                "instance_id": instance_id,
                "username": mapping_info["username"],
                "project_code": mapping_info["project_code"],
                "project_name": mapping_info["project_name"],
                "cost_center": mapping_info["cost_center"],
                "instance_type": mapping_info["instance_type"],
                "infrastructure_type": mapping_info["infrastructure_type"],
                "parent_cluster": mapping_info["parent_cluster"],
                "queue_name": mapping_info["queue_name"],
                "budget_limit": mapping_info["budget_limit"],
                "gpu_occupancy": get_gpu_occupancy(),
                "gpu_count": get_gpu_count(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "vcpu_count": psutil.cpu_count(),
                "memory": {
                    "percent": psutil.virtual_memory().percent,
                    "used_gb": round(psutil.virtual_memory().used / (1024**3), 2),
                    "total_gb": round(psutil.virtual_memory().total / (1024**3), 2)
                },
                "slurm_job_id": get_slurm_job_id()
            }
            
            key = f"metrics/year={now.year}/month={now.month:02d}/day={now.day:02d}/hour={now.hour:02d}/{instance_id}_{now.minute:02d}.json"
            s3.put_object(
                Bucket="mogam-or-cur-stg",
                Key=key,
                Body=json.dumps(metrics, indent=2)
            )
            print(f"SUCCESS: {instance_id}")
            time.sleep(60)
        except Exception as e:
            print(f"ERROR: {e}")
            time.sleep(60)

if __name__ == "__main__":
    collect_and_upload()
