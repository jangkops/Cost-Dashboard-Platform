#!/usr/bin/env python3
import os
import sys
import time
import json
import subprocess
import boto3
from datetime import datetime

S3_BUCKET = "mogam-or-cur-stg"
S3_PREFIX = "metrics/"
INTERVAL = 60

s3 = boto3.client("s3", region_name="us-west-2")

def get_instance_id():
    try:
        import urllib.request
        token_url = "http://169.254.169.254/latest/api/token"
        token_req = urllib.request.Request(token_url, headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"}, method="PUT")
        token = urllib.request.urlopen(token_req, timeout=2).read().decode()
        
        id_url = "http://169.254.169.254/latest/meta-data/instance-id"
        id_req = urllib.request.Request(id_url, headers={"X-aws-ec2-metadata-token": token})
        return urllib.request.urlopen(id_req, timeout=2).read().decode()
    except:
        return os.environ.get("INSTANCE_ID", "unknown")

def get_instance_type():
    try:
        import urllib.request
        token_url = "http://169.254.169.254/latest/api/token"
        token_req = urllib.request.Request(token_url, headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"}, method="PUT")
        token = urllib.request.urlopen(token_req, timeout=2).read().decode()
        
        type_url = "http://169.254.169.254/latest/meta-data/instance-type"
        type_req = urllib.request.Request(type_url, headers={"X-aws-ec2-metadata-token": token})
        return urllib.request.urlopen(type_req, timeout=2).read().decode()
    except:
        return "unknown"

def has_gpu():
    return os.path.exists("/dev/nvidia0")

def load_tmux_paths():
    """Load tmux session paths from running tmux processes via /proc"""
    paths = {}
    try:
        result = subprocess.run(
            ["ps", "-eo", "pid,cmd"],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.split("\n"):
            if "tmux" not in line or "grep" in line or "ps -eo" in line:
                continue
            
            parts = line.strip().split(None, 1)
            if len(parts) < 2:
                continue
                
            pid = parts[0]
            if not pid.isdigit():
                continue
                
            try:
                cwd = os.readlink(f"/host_proc/{pid}/cwd")
                if cwd and cwd != "/":
                    # Use PID as unique identifier
                    paths[f"tmux_{pid}"] = cwd
            except (OSError, FileNotFoundError):
                # Process may have terminated, skip
                continue
    except subprocess.TimeoutExpired:
        print("Warning: tmux path loading timed out")
    except Exception as e:
        print(f"Error loading tmux paths: {e}")
    return paths

def load_vscode_paths():
    """Load vscode workspace paths from running vscode-server processes via /proc"""
    paths = {}
    try:
        result = subprocess.run(
            ["ps", "-eo", "pid,cmd"],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.split("\n"):
            if "vscode-server" not in line or "grep" in line or "ps -eo" in line:
                continue
            
            parts = line.strip().split(None, 1)
            if len(parts) < 2:
                continue
                
            pid = parts[0]
            if not pid.isdigit():
                continue
                
            try:
                cwd = os.readlink(f"/host_proc/{pid}/cwd")
                # Accept all valid paths except root
                if cwd and cwd != "/" and len(cwd) > 1:
                    # Use PID as unique identifier
                    paths[f"vscode_{pid}"] = cwd
            except (OSError, FileNotFoundError):
                # Process may have terminated, skip
                continue
    except subprocess.TimeoutExpired:
        print("Warning: vscode path loading timed out")
    except Exception as e:
        print(f"Error loading vscode paths: {e}")
    return paths

def extract_project_from_path(cwd, tmux_paths={}, vscode_paths={}, pid=None):
    # Support /opt/ paths (extract last directory name)
    if cwd.startswith("/opt/"):
        parts = cwd.rstrip("/").split("/")
        if len(parts) >= 2:
            return parts[-1]  # Return last directory name
    
    
    # Support /workspace/ paths (bind-mounted from /home/user/project)
    elif cwd.startswith("/workspace/"):
        parts = cwd.replace("/workspace/", "").split("/")
        if len(parts) >= 1 and parts[0]:
            return parts[0]  # /workspace/PROJECT_NAME/...

    # Support /local_nvme/ paths (P5 NVMe storage)
    elif cwd.startswith("/local_nvme/"):
        parts = cwd.replace("/local_nvme/", "").split("/")
        if len(parts) >= 3 and parts[1] == "project":
            return parts[2]  # username/project/PROJECT_NAME
        elif len(parts) >= 2:
            return parts[1]  # username/PROJECT_NAME

    # Support /home/ paths
    elif cwd.startswith("/home/"):
        parts = cwd.replace("/home/", "").split("/")
        if len(parts) >= 2:
            return parts[1]  # username/project format
    
    return "unknown"

def get_gpu_processes(tmux_paths, vscode_paths):
    """Get GPU processes with GPU device mapping"""
    try:
        # Get GPU process to device mapping
        result = subprocess.run(
            ["nvidia-smi", "--query-compute-apps=gpu_uuid,pid,used_memory", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return []
        
        # Build GPU UUID to ID mapping
        gpu_uuid_result = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,gpu_uuid", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=30
        )
        gpu_uuid_to_id = {}
        for line in gpu_uuid_result.stdout.strip().split("\n"):
            if line.strip():
                parts = line.split(",")
                if len(parts) >= 2:
                    gpu_id = int(parts[0].strip())
                    gpu_uuid = parts[1].strip()
                    gpu_uuid_to_id[gpu_uuid] = gpu_id
        
        # Group processes by PID
        pid_to_gpus = {}
        pid_to_mem = {}
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split(",")
            if len(parts) >= 3:
                gpu_uuid = parts[0].strip()
                pid = int(parts[1].strip())
                gpu_mem = int(parts[2].strip())
                
                gpu_id = gpu_uuid_to_id.get(gpu_uuid, 0)
                
                if pid not in pid_to_gpus:
                    pid_to_gpus[pid] = []
                    pid_to_mem[pid] = 0
                
                pid_to_gpus[pid].append(gpu_id)
                pid_to_mem[pid] += gpu_mem
        
        processes = []
        for pid, gpu_devices in pid_to_gpus.items():
            try:
                with open(f"/host_proc/{pid}/comm", "r") as f:
                    name = f.read().strip()
                cwd = os.readlink(f"/host_proc/{pid}/cwd")
                with open(f"/host_proc/{pid}/stat", "r") as f:
                    stat = f.read().split()
                    ppid = int(stat[3])
                
                # Get username
                username = "unknown"
                try:
                    with open(f"/host_proc/{pid}/status", "r") as f:
                        for line in f:
                            if line.startswith("Uid:"):
                                uid = int(line.split()[1])
                                try:
                                    import pwd
                                    username = pwd.getpwuid(uid).pw_name
                                except KeyError:
                                    username = f"uid_{uid}"
                                break
                except:
                    pass
                
                # Get CPU percent
                with open(f"/host_proc/{pid}/stat", "r") as f:
                    stat_data = f.read().split()
                    utime = int(stat_data[13])
                    stime = int(stat_data[14])
                    cpu_percent = (utime + stime) / 100.0  # Simplified
                
            except Exception as e:
                print(f"Error reading process {pid}: {e}")
                continue
            
            project = extract_project_from_path(cwd, tmux_paths, vscode_paths, pid)
            
            # If cwd is /, check parent process cwd
            if project == "unknown" and cwd == "/":
                try:
                    ppid_cwd = os.readlink(f"/host_proc/{ppid}/cwd")
                    project = extract_project_from_path(ppid_cwd, tmux_paths, vscode_paths, ppid)
                except:
                    pass
            
            if project.endswith("_홈"):
                project = extract_project_from_path(cwd, tmux_paths, vscode_paths, ppid)
                if project == "unknown" or project.endswith("_홈"):
                    try:
                        with open(f"/host_proc/{ppid}/stat", "r") as f:
                            gppid = int(f.read().split()[3])
                        gppid_cwd = os.readlink(f"/host_proc/{gppid}/cwd")
                        project = extract_project_from_path(gppid_cwd, tmux_paths, vscode_paths, gppid)
                    except:
                        pass
            
            if project.endswith("_홈") or project == "unknown":
                project = extract_project_from_path(cwd)
            
            processes.append({
                "pid": pid,
                "username": username,
                "project": project,
                "cpu_percent": cpu_percent,
                "gpu_devices": sorted(gpu_devices),
                "gpu_count": len(gpu_devices),
                "gpu_memory_mb": pid_to_mem[pid],
                "command": name
            })
        
        return processes
    except Exception as e:
        print(f"Error getting GPU processes: {e}")
        return []


def scan_proc_filesystem():
    """Scan /proc directly for all processes"""
    processes = []
    try:
        for pid_dir in os.listdir('/proc'):
            if not pid_dir.isdigit():
                continue
            
            pid = int(pid_dir)
            try:
                # Read cmdline
                with open(f'/host_proc/{pid}/cmdline', 'r') as f:
                    cmdline = f.read().replace('\x00', ' ').strip()
                
                if not cmdline:
                    continue
                
                # Read cwd
                try:
                    cwd = os.readlink(f'/host_proc/{pid}/cwd')
                except:
                    cwd = ''
                
                # Read status for username
                username = 'unknown'
                try:
                    with open(f'/host_proc/{pid}/status', 'r') as f:
                        for line in f:
                            if line.startswith('Uid:'):
                                uid = int(line.split()[1])
                                try:
                                    import pwd
                                    username = pwd.getpwuid(uid).pw_name
                                except:
                                    username = f'uid_{uid}'
                                break
                except:
                    pass
                
                processes.append({
                    'pid': pid,
                    'cmdline': cmdline,
                    'cwd': cwd,
                    'username': username
                })
            except:
                continue
    except Exception as e:
        print(f"Error scanning /proc: {e}")
    
    return processes



def get_slurm_job_info(pid):
    """Get Slurm job info from process tree"""
    try:
        # Check if process is under slurmstepd
        current_pid = pid
        for _ in range(10):  # Max 10 levels up
            try:
                with open(f'/host_proc/{current_pid}/status', 'r') as f:
                    status = f.read()
                    # Get parent PID
                    ppid_match = re.search(r'PPid:\s+(\d+)', status)
                    if not ppid_match:
                        break
                    parent_pid = int(ppid_match.group(1))
                    
                    # Check parent cmdline
                    with open(f'/host_proc/{parent_pid}/cmdline', 'r') as cf:
                        parent_cmd = cf.read().replace('\x00', ' ')
                        if 'slurmstepd' in parent_cmd:
                            # Extract job ID from slurmstepd command
                            job_match = re.search(r'--jobid=(\d+)', parent_cmd)
                            if job_match:
                                return {'job_id': job_match.group(1), 'is_slurm': True}
                    
                    current_pid = parent_pid
            except:
                break
    except:
        pass
    return {'is_slurm': False}


def get_cpu_processes(tmux_paths, vscode_paths):
    """Get CPU processes from /local_nvme/, /home/, /opt/ with project info"""
    try:
        result = subprocess.run(
            ["ps", "-eo", "pid,comm,pcpu,user", "--no-headers"],
            capture_output=True, text=True, timeout=30
        )
        
        processes = []
        for line in result.stdout.strip().split("\n"):
            parts = line.split()
            if len(parts) < 4:
                continue
            
            # Handle multi-word comm fields (e.g., "UVM global queu")
            # Format: PID COMM... PCPU USER
            # Strategy: PID is first, USER is last, PCPU is second-to-last
            try:
                pid = int(parts[0])
                username = parts[-1]
                cpu = float(parts[-2])
                name = parts[1]  # Use first word of comm
            except (ValueError, IndexError):
                continue
            
            try:
                cwd = os.readlink(f"/host_proc/{pid}/cwd")
            except:
                continue
            
            # P5: /local_nvme/, /home/, /opt/ 경로만 추적
            if not (cwd.startswith("/home/") or 
                    cwd.startswith("/opt/") or cwd.startswith("/local_nvme/") or
                    cwd.startswith("/workspace/")):
                continue
            
            if name not in ["python", "python3", "java"]:
                continue
            
            project = extract_project_from_path(cwd, tmux_paths, vscode_paths, pid)
            
            processes.append({
                "pid": pid,
                "username": username,
                "project": project,
                "cpu_percent": cpu,
                "gpu_devices": None,
                "gpu_count": 0,
                "gpu_memory_mb": 0,
                "command": name
            })
        
        return processes
    except Exception as e:
        print(f"Error getting CPU processes: {e}")
        return []

def get_gpu_utilization():
    """Get GPU utilization stats"""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,utilization.gpu,utilization.memory,memory.used,memory.total", 
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=30
        )
        
        stats = []
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                parts = line.split(",")
                if len(parts) >= 5:
                    stats.append({
                        "gpu_id": int(parts[0].strip()),
                        "gpu_util": float(parts[1].strip()),
                        "mem_util": float(parts[2].strip()),
                        "mem_used_mb": float(parts[3].strip()),
                        "mem_total_mb": float(parts[4].strip())
                    })
        return stats
    except:
        return []

def upload_to_s3(data, instance_id):
    timestamp = int(time.time())
    key = f"{S3_PREFIX}enhanced_v2/{datetime.utcnow().strftime('%Y/%m/%d/%H')}/enhanced-{timestamp}.json"
    
    try:
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=json.dumps(data)
        )
        print(f"Uploaded to s3://{S3_BUCKET}/{key}")
    except Exception as e:
        print(f"Upload failed: {e}")

def main():
    instance_id = get_instance_id()
    instance_type = get_instance_type()
    gpu_mode = has_gpu()
    
    print(f"Enhanced Agent v2.5 GPU Enhanced started")
    print(f"Instance: {instance_id} ({instance_type})")
    print(f"Mode: {'GPU' if gpu_mode else 'CPU'}")
    
    while True:
        try:
            print(f"[{datetime.utcnow().isoformat()}] Starting collection cycle...")
            
            print("Loading tmux paths...")
            tmux_paths = load_tmux_paths()
            print(f"Loaded {len(tmux_paths)} tmux paths")
            
            print("Loading vscode paths...")
            vscode_paths = load_vscode_paths()
            print(f"Loaded {len(vscode_paths)} vscode paths")
            
            if gpu_mode:
                print("Collecting GPU processes...")
                gpu_processes = get_gpu_processes(tmux_paths, vscode_paths)
                print(f"Found {len(gpu_processes)} GPU processes")
                
                print("Collecting CPU processes...")
                cpu_processes = get_cpu_processes(tmux_paths, vscode_paths)
                print(f"Found {len(cpu_processes)} CPU processes")
                
            #墨�n���ƭy߾