from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.executors.cpp_executor import run_cpp
from app.executors.java_executor import run_java
from app.executors.python_executor import run_python
from app.models.testcase_model import TestCase
from app.services.evaluation_service import evaluate

EXECUTOR_MAP = {
    "python": run_python,
    "cpp": run_cpp,
    "c++": run_cpp,
    "java": run_java,
}


def execute_submission(
    language: str,
    code: str,
    problem_id: Optional[int] = None,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """
    Language dispatch table & testcase-based grading pipeline.
    Loads TestCase rows for problem_id, runs sandboxed code per case, diffs via evaluate(),
    and computes aggregate verdict.
    """
    lang_key = (language or "").lower().strip()
    executor = EXECUTOR_MAP.get(lang_key)

    if not executor:
        return {
            "verdict": "Compilation Error",
            "output": f"Unsupported programming language: '{language}'",
            "passed_test_cases": 0,
            "total_test_cases": 0,
        }

    test_cases: List[TestCase] = []
    if problem_id is not None and db is not None:
        test_cases = (
            db.query(TestCase).filter(TestCase.problem_id == problem_id).all()
        )

    if not test_cases:
        res = executor(code, input_data="", timeout_s=5)
        if res.get("compilation_error"):
            verdict = "Compilation Error"
        elif res.get("timed_out"):
            verdict = "Time Limit Exceeded"
        elif res.get("exit_code", 0) != 0:
            verdict = "Runtime Error"
        else:
            verdict = "Accepted"

        output_text = res.get("stdout") or res.get("stderr") or "Executed successfully."
        return {
            "verdict": verdict,
            "output": output_text,
            "passed_test_cases": 1 if verdict == "Accepted" else 0,
            "total_test_cases": 1,
        }

    total_cases = len(test_cases)
    passed_cases = 0
    final_verdict = "Accepted"
    output_logs = []

    for idx, tc in enumerate(test_cases, start=1):
        res = executor(code, input_data=tc.input_data or "", timeout_s=5)

        if res.get("compilation_error"):
            final_verdict = "Compilation Error"
            output_logs.append(
                f"Test case {idx}/{total_cases}: Compilation Error\n{res.get('stderr', '')}"
            )
            break
        elif res.get("timed_out"):
            final_verdict = "Time Limit Exceeded"
            output_logs.append(f"Test case {idx}/{total_cases}: Time Limit Exceeded")
            break
        elif res.get("exit_code", 0) != 0:
            final_verdict = "Runtime Error"
            output_logs.append(
                f"Test case {idx}/{total_cases}: Runtime Error\n{res.get('stderr', '')}"
            )
            break

        actual_stdout = res.get("stdout", "")
        if evaluate(actual_stdout, tc.expected_output or ""):
            passed_cases += 1
            output_logs.append(f"Test case {idx}/{total_cases}: Passed")
        else:
            final_verdict = "Wrong Answer"
            output_logs.append(
                f"Test case {idx}/{total_cases}: Wrong Answer\n"
                f"Expected: {tc.expected_output}\nGot: {actual_stdout}"
            )
            break

    summary = (
        f"Verdict: {final_verdict} ({passed_cases}/{total_cases} test cases passed)\n"
        + "\n".join(output_logs)
    )

    return {
        "verdict": final_verdict,
        "output": summary,
        "passed_test_cases": passed_cases,
        "total_test_cases": total_cases,
    }