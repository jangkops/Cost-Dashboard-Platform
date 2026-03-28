import subprocess
import json
import os
import re

BASE_DIR = "/home/app/ansible"

def run_playbook(playbook_path, extra_vars=None):
    abs_path = os.path.join(BASE_DIR, playbook_path)

    cmd = [
        "ansible-playbook",
        abs_path,
    ]

    if extra_vars:
        cmd += ["--extra-vars", json.dumps(extra_vars)]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=BASE_DIR
        )
        
        stdout = result.stdout
        
        # Parse Ansible output for actual success/failure
        failed_pattern = r'failed=(\d+)'
        unreachable_pattern = r'unreachable=(\d+)'
        
        failed_match = re.search(failed_pattern, stdout)
        unreachable_match = re.search(unreachable_pattern, stdout)
        
        failed_count = int(failed_match.group(1)) if failed_match else 0
        unreachable_count = int(unreachable_match.group(1)) if unreachable_match else 0
        
        # Check for skip status only if returncode is 0 and no failures
        if result.returncode == 0 and failed_count == 0 and unreachable_count == 0 and "SKIP:" in stdout:
            return {
                "status": "skipped",
                "stdout": stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "error": ""
            }
        
        success = (result.returncode == 0 and failed_count == 0 and unreachable_count == 0)
        
        # Extract error message from stdout for failed tasks
        error_msg = ""
        if not success:
            # Try to extract meaningful error from stdout
            error_patterns = [
                r'stdout: (.+?)(?:\n  stdout_lines:|$)',
                r'Error: (.+?)(?:\n|$)',
                r'msg: (.+?)(?:\n|$)',
                r'fatal: \[.+?\]: FAILED! => (.+?)(?:\n\n|$)'
            ]
            
            for pattern in error_patterns:
                match = re.search(pattern, stdout, re.DOTALL)
                if match:
                    error_msg = match.group(1).strip()
                    # Limit error message length
                    if len(error_msg) > 200:
                        error_msg = error_msg[:200] + "..."
                    break
            
            if not error_msg and result.stderr:
                error_msg = result.stderr.strip()[:200]
        
        return {
            "status": "success" if success else "failed",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "error": error_msg
        }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }
