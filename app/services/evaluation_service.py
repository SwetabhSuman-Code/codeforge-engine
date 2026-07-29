def evaluate(actual_output: str, expected_output: str) -> bool:
    """
    Diffs actual stdout against expected output.
    Returns True if stdout matches expected_output (ignoring trailing whitespace/newlines).
    """
    actual_clean = "\n".join([line.rstrip() for line in (actual_output or "").strip().splitlines()])
    expected_clean = "\n".join([line.rstrip() for line in (expected_output or "").strip().splitlines()])
    return actual_clean == expected_clean