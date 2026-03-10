import subprocess
import tempfile

def run_python(code: str):

    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as temp_file:

        temp_file.write(code.encode())
        temp_file_path = temp_file.name

    try:

        result = subprocess.run(
            ["python", temp_file_path],
            capture_output=True,
            text=True,
            timeout=2
        )

        return result.stdout, result.stderr

    except subprocess.TimeoutExpired:

        return "", "Time Limit Exceeded"