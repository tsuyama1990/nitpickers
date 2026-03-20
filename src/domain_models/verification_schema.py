from pydantic import BaseModel, ConfigDict, Field


class VerificationResult(BaseModel):
    """
    Result of a single mechanical verification step (linting, typing, or testing).
    """

    model_config = ConfigDict(extra="forbid")

    command: str = Field(..., description="The command executed")
    exit_code: int = Field(..., description="Integer exit code returned by the shell")
    stdout: str = Field(default="", description="Full standard output")
    stderr: str = Field(default="", description="Critical standard error traceback")
    timeout_occurred: bool = Field(default=False, description="Whether the command timed out")

    @property
    def passed(self) -> bool:
        """Returns True if the exit code is 0 and no timeout occurred."""
        return self.exit_code == 0 and not self.timeout_occurred


class StructuralGateReport(BaseModel):
    """
    Aggregated report of all mechanical verification checks.
    Provides a comprehensive snapshot of the system's structural integrity.
    """

    model_config = ConfigDict(extra="forbid")

    lint_result: VerificationResult = Field(..., description="Result of the linting process")
    type_check_result: VerificationResult = Field(
        ..., description="Result of the type checking process"
    )
    test_result: VerificationResult = Field(..., description="Result of the testing process")

    @property
    def passed(self) -> bool:
        """Returns True if all underlying verification checks passed."""
        return self.lint_result.passed and self.type_check_result.passed and self.test_result.passed

    def get_failure_report(self) -> str:
        """
        Generates a consolidated failure report containing the stderr of failing checks.
        If stderr is empty but the check failed, includes stdout as a fallback.
        """
        report_lines = []
        for name, result in [
            ("Linting", self.lint_result),
            ("Type Checking", self.type_check_result),
            ("Testing", self.test_result),
        ]:
            if not result.passed:
                report_lines.append(f"--- {name} Failed ---")
                report_lines.append(f"Command: {result.command}")
                if result.timeout_occurred:
                    report_lines.append("Reason: TIMEOUT OCCURRED")
                report_lines.append(f"Exit Code: {result.exit_code}")
                # Use stderr if available, fallback to stdout, else empty
                err_msg = result.stderr.strip() if result.stderr.strip() else result.stdout.strip()
                report_lines.append(f"Output:\n{err_msg}\n")
        return "\n".join(report_lines)
