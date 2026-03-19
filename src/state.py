from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .config import settings
from .domain_models import (
    AuditResult,
    ConflictRegistryItem,
    CyclePlan,
    FileOperation,
    FixPlan,
    UatAnalysis,
    UATResult,
)
from .enums import FlowStatus, WorkPhase


class CycleState(BaseModel):
    """LangGraph state for the development cycle."""

    # Required fields
    cycle_id: str = Field(...)

    # Committee State with validation
    current_auditor_index: int = Field(
        default=1, ge=1, description="Current auditor (1-based index)"
    )
    current_auditor_review_count: int = Field(
        default=1, ge=1, description="Current review count for this auditor"
    )
    iteration_count: int = Field(default=0, ge=0)

    # Session Persistence
    jules_session_name: str | None = Field(default=None)
    critic_retry_count: int = Field(default=0)
    pr_url: str | None = Field(default=None)
    resume_mode: bool = Field(default=False)
    active_branch: str | None = Field(default=None)

    # Audit State
    audit_result: AuditResult | None = Field(default=None)
    audit_feedback: list[str] = Field(default_factory=list)
    audit_pass_count: int = Field(default=0)
    audit_retries: int = Field(default=0)
    audit_logs: str = Field(default="")

    # QA/Tutorial State
    qa_retry_count: int = Field(default=0)

    # Test State
    test_logs: str = Field(default="")
    test_exit_code: int | None = Field(default=None)
    uat_analysis: UatAnalysis | None = Field(default=None)
    sandbox_artifacts: dict[str, Any] = Field(default_factory=dict)

    # UAT State
    uat_exit_code: int = Field(default=0)
    uat_artifacts: UATResult | None = Field(default=None)
    current_fix_plan: FixPlan | None = Field(default=None)
    conflict_status: FlowStatus | None = Field(default=None)
    concurrent_dependencies: list[str] = Field(default_factory=list)
    tdd_phase: Literal["red", "green"] | None = Field(default=None)

    # Phase Tracking
    current_phase: WorkPhase = Field(default=WorkPhase.INIT)
    error: str | None = Field(default=None)
    # Add status explicitely to allow safe access
    status: FlowStatus | None = Field(default=None)
    last_audited_commit: str | None = Field(default=None)

    # Legacy/Optional Fields
    sandbox_id: str | None = Field(default=None)
    plan: CyclePlan | None = Field(default=None)
    code_changes: list[FileOperation] = Field(default_factory=list)
    loop_count: int = Field(default=0)
    correction_history: list[str] = Field(default_factory=list)
    dry_run: bool = Field(default=False)
    interactive: bool = Field(default=False)
    goal: str | None = Field(default=None)
    approved: bool | None = Field(default=None)
    coder_report: dict[str, Any] | None = Field(default=None)
    planned_cycles: list[str] = Field(default_factory=list)

    # Session tracking
    project_session_id: str | None = Field(default=None)
    feature_branch: str | None = Field(default=None)  # Main development branch
    integration_branch: str | None = Field(default=None)  # Final integration branch
    is_session_finalized: bool = Field(default=False)
    final_fix: bool = Field(
        default=False, description="Flag indicating final fix before merge (bypass further audits)"
    )

    # Architect Config
    planned_cycle_count: int | None = Field(
        default=None, ge=1, description="Planned cycle count from configuration"
    )
    requested_cycle_count: int | None = Field(
        default=None, description="User-requested cycle count from CLI"
    )

    # Validators
    @field_validator("current_auditor_index")
    @classmethod
    def validate_auditor_index(cls, v: int) -> int:
        if v > settings.NUM_AUDITORS:
            msg = f"Auditor index {v} exceeds NUM_AUDITORS={settings.NUM_AUDITORS}"
            raise ValueError(msg)
        return v

    @field_validator("current_auditor_review_count")
    @classmethod
    def validate_review_count(cls, v: int) -> int:
        if v > settings.REVIEWS_PER_AUDITOR:
            msg = f"Review count {v} exceeds REVIEWS_PER_AUDITOR={settings.REVIEWS_PER_AUDITOR}"
            raise ValueError(msg)
        return v

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)

    # LangGraph internally injects these
    langgraph_step: int | None = Field(default=None)
    langgraph_node: str | None = Field(default=None)
    langgraph_triggers: list[Any] | None = Field(default=None)
    langgraph_path: tuple[Any, ...] | None = Field(default=None)
    langgraph_checkpoint: dict[str, Any] | None = Field(default=None)

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class IntegrationState(BaseModel):
    """LangGraph state for Master Integrator concurrent execution."""

    master_integrator_session_id: str | None = Field(default=None)
    unresolved_conflicts: list[ConflictRegistryItem] = Field(default_factory=list)

    langgraph_step: int | None = Field(default=None)
    langgraph_node: str | None = Field(default=None)
    langgraph_triggers: list[Any] | None = Field(default=None)
    langgraph_path: tuple[Any, ...] | None = Field(default=None)
    langgraph_checkpoint: dict[str, Any] | None = Field(default=None)

    model_config = ConfigDict(extra="forbid", validate_assignment=True)
