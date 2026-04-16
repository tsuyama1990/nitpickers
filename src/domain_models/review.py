from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ReviewIssue(BaseModel):
    """個別の指摘事項"""

    model_config = ConfigDict(extra="forbid")

    category: Literal[
        "Hardcoding",
        "Scalability",
        "Security",
        "Architecture",
        "Type Safety",
        "Logic Error",
        "Test Coverage",
        "Other",
    ] = Field(description="Issue category. Be highly sensitive to 'Hardcoding'.")
    severity: Literal["fatal", "warning"] = Field(
        description="'fatal' MUST be used for SPEC violations and Hardcoding. 'warning' is for non-blocking boy-scout suggestions."
    )
    file_path: str = Field(description="Exact file path where the issue is found.")
    target_code_snippet: str = Field(
        description="The specific snippet of code containing the issue (1-3 lines max) to help the Coder locate it via string search."
    )
    issue_description: str = Field(
        description="Clear and concise description of why this is an issue."
    )
    concrete_fix: str = Field(
        description="EXACT code or structural change required. For 'Hardcoding', explicitly state WHERE to move the constant."
    )


class AuditorReport(BaseModel):
    """レポート全体"""

    model_config = ConfigDict(extra="forbid")

    is_passed: bool = Field(
        description="Must be False if there is at least one issue. Set to True ONLY if there are zero issues."
    )
    summary: str = Field(description="Brief 2-3 sentence summary of the review.")
    issues: list[ReviewIssue] = Field(
        default_factory=list,
        description="Issues that MUST be fixed. You MUST include any Hardcoding of URLs, API keys, paths, or magic numbers here.",
    )


class AuditResult(BaseModel):
    """Audit result"""

    model_config = ConfigDict(extra="forbid")
    status: str | None = None
    is_approved: bool = False
    reason: str | None = None
    feedback: str | None = None
    critical_issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class PlanAuditResult(BaseModel):
    """Result of AI-on-AI Plan Audit"""

    model_config = ConfigDict(extra="forbid")
    status: Literal["APPROVED", "REJECTED"]
    reason: str
    feedback: str | None = Field(default="", description="Mandatory if REJECTED")
