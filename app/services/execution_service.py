from app.executors.python_executor import run_python

def execute_submission(code: str):

    output, error = run_python(code)

    return {
        "output": output,
        "error": error
    }