import os
import sys
from typing import Any, Dict

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
docker_dir = os.path.join(repo_root, "docker")
if docker_dir not in sys.path:
    sys.path.insert(0, docker_dir)

from docker_executor import run_in_sandbox


def run_python(code: str, input_data: str = "", timeout_s: int = 5) -> Dict[str, Any]:
    """
    Executes Python code inside the sandbox container environment.
    """
    return run_in_sandbox("python", code, input_data=input_data, timeout_s=timeout_s)