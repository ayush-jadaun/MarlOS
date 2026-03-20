Run the MarlOS test suite.

If $ARGUMENTS is provided, run only tests matching that pattern.
Otherwise run the full suite (excluding integration tests).

Steps:
1. Run: `python -m pytest test/ --ignore=test/integration -v --timeout=30 $ARGUMENTS`
2. Show a summary of pass/fail counts
3. For any failures, show the error and propose a fix
