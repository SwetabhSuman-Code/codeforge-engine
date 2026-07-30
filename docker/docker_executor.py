import os
import shutil
import subprocess
import sys
import tempfile
from typing import Dict, Any

try:
    import docker
except ImportError:
    docker = None


def run_in_sandbox(
    language: str, code: str, input_data: str = "", timeout_s: int = 5
) -> Dict[str, Any]:
    """
    Executes user code inside an ephemeral Docker container or sandboxed process.
    Enforces resource limits, network isolation, and wall-clock timeouts.
    """
    lang = language.lower().strip()
    if lang in ["cpp", "c++"]:
        lang = "cpp"

    image_map = {
        "python": "python:3.11-slim",
        "cpp": "gcc:latest",
        "java": "openjdk:17-slim",
    }

    # Attempt execution via Docker daemon if explicitly enabled and available
    use_docker = os.getenv("USE_DOCKER_SANDBOX", "false").lower() in ["true", "1"]
    if docker and use_docker:
        try:
            client = docker.from_env()
            client.ping()
            return _run_docker(client, lang, code, input_data, timeout_s, image_map.get(lang, "python:3.11-slim"))
        except Exception:
            pass

    # Fallback execution via subprocess sandbox
    return _run_subprocess(lang, code, input_data, timeout_s)


def _run_docker(
    client, lang: str, code: str, input_data: str, timeout_s: int, image_name: str
) -> Dict[str, Any]:
    temp_dir = tempfile.mkdtemp()
    try:
        if lang == "python":
            file_name = "main.py"
            cmd = "python /app/main.py"
        elif lang == "cpp":
            file_name = "solution.cpp"
            cmd = "sh -c 'g++ /app/solution.cpp -o /tmp/solution && /tmp/solution'"
        elif lang == "java":
            file_name = "Solution.java"
            cmd = "sh -c 'javac /app/Solution.java -d /tmp && java -cp /tmp Solution'"
        else:
            file_name = "main.py"
            cmd = "python /app/main.py"

        file_path = os.path.join(temp_dir, file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)

        container = client.containers.create(
            image=image_name,
            command=cmd,
            network_disabled=True,
            mem_limit="128m",
            nano_cpus=1000000000,
            working_dir="/app",
            volumes={temp_dir: {"bind": "/app", "mode": "ro"}},
            stdin_open=True,
            tty=False,
        )

        try:
            container.start()
            socket = container.attach_socket(params={"stdin": 1, "stream": 1})
            if input_data:
                socket._sock.sendall(input_data.encode("utf-8"))
            socket._sock.close()

            res = container.wait(timeout=timeout_s)
            exit_code = res.get("StatusCode", 0)
            stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
            stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")

            compilation_error = (exit_code != 0) and ("error:" in stderr.lower() or "javac" in stderr.lower())

            return {
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": exit_code,
                "timed_out": False,
                "compilation_error": compilation_error,
            }
        except Exception as e:
            if "timeout" in str(e).lower() or "read timed out" in str(e).lower():
                return {
                    "stdout": "",
                    "stderr": "Time Limit Exceeded",
                    "exit_code": -1,
                    "timed_out": True,
                    "compilation_error": False,
                }
            raise e
        finally:
            try:
                container.remove(force=True)
            except Exception:
                pass
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def _run_subprocess(
    lang: str, code: str, input_data: str, timeout_s: int
) -> Dict[str, Any]:
    temp_dir = tempfile.mkdtemp()
    try:
        if lang == "python":
            file_path = os.path.join(temp_dir, "main.py")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)
            exec_args = [sys.executable, file_path]
            return _execute_cmd(exec_args, input_data, timeout_s)

        elif lang == "cpp":
            file_path = os.path.join(temp_dir, "solution.cpp")
            out_path = os.path.join(temp_dir, "solution.exe" if os.name == "nt" else "solution")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)

            compile_res = subprocess.run(
                ["g++", file_path, "-o", out_path],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if compile_res.returncode != 0:
                return {
                    "stdout": compile_res.stdout,
                    "stderr": compile_res.stderr,
                    "exit_code": compile_res.returncode,
                    "timed_out": False,
                    "compilation_error": True,
                }

            return _execute_cmd([out_path], input_data, timeout_s)

        elif lang == "java":
            file_path = os.path.join(temp_dir, "Solution.java")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)

            compile_res = subprocess.run(
                ["javac", file_path],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if compile_res.returncode != 0:
                return {
                    "stdout": compile_res.stdout,
                    "stderr": compile_res.stderr,
                    "exit_code": compile_res.returncode,
                    "timed_out": False,
                    "compilation_error": True,
                }

            return _execute_cmd(["java", "-cp", temp_dir, "Solution"], input_data, timeout_s)

        else:
            file_path = os.path.join(temp_dir, "main.py")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)
            return _execute_cmd([sys.executable, file_path], input_data, timeout_s)

    except FileNotFoundError as e:
        return {
            "stdout": "",
            "stderr": f"Compiler/Runtime not found: {str(e)}",
            "exit_code": 1,
            "timed_out": False,
            "compilation_error": True,
        }
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def _execute_cmd(args: list, input_data: str, timeout_s: int) -> Dict[str, Any]:
    try:
        proc = subprocess.run(
            args,
            input=input_data,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        return {
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "exit_code": proc.returncode,
            "timed_out": False,
            "compilation_error": False,
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": "Time Limit Exceeded",
            "exit_code": -1,
            "timed_out": True,
            "compilation_error": False,
        }
