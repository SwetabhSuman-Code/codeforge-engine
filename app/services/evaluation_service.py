def evaluate(output, expected):

    if output.strip() == expected.strip():
        return "Accepted"

    return "Wrong Answer"