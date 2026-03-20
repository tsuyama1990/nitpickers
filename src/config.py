import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.domain_models.tracing import LangSmithConfig

# Load environment variables from .env file
# Priority: .ac_cdd/.env > .env (root)
_ac_cdd_env = Path.cwd() / ".ac_cdd" / ".env"
_root_env = Path.cwd() / ".env"

try:
    if _ac_cdd_env.exists():
        load_dotenv(_ac_cdd_env, override=True)
    elif _root_env.exists():
        load_dotenv(_root_env, override=True)
except Exception:
    logging.exception("Could not load dotenv")

# Constants
PROMPT_FILENAME_MAP = {
    "auditor.md": "AUDITOR_INSTRUCTION.md",
    "coder.md": "CODER_INSTRUCTION.md",
    "architect.md": "ARCHITECT_INSTRUCTION.md",
}


def _check_env_pkg_dir() -> str | None:
    env_pkg_dir = os.getenv("PACKAGE_DIR")
    if env_pkg_dir:
        try:
            resolved_pkg = Path(env_pkg_dir).resolve()
            if resolved_pkg.exists() and resolved_pkg.is_relative_to(Path.cwd()):
                return str(resolved_pkg)
        except (ValueError, RuntimeError):
            pass
    return None

def _check_docker_src_path() -> str | None:
    docker_src_path = os.getenv("DOCKER_SRC_PATH")
    if docker_src_path:
        docker_path = Path(docker_src_path)
        if docker_path.exists():
            return str(docker_path)
    return None

def _check_dev_src_path() -> str | None:
    dev_src_path = os.getenv("DEV_SRC_PATH")
    if dev_src_path:
        src_path = Path(dev_src_path)
        if src_path.exists():
            for p in src_path.iterdir():
                if p.is_dir() and (p / "__init__.py").exists():
                    return str(p)
    return None

def _detect_package_dir() -> str:
    """Detects the main package directory."""
    res = _check_env_pkg_dir()
    if res:
        return res

    res = _check_docker_src_path()
    if res:
        return res

    res = _check_dev_src_path()
    if res:
        return res

    default_src_dir = os.getenv("DEFAULT_SRC_DIR")
    if default_src_dir:
        return default_src_dir

    src_fallback = Path.cwd() / "src"
    if src_fallback.exists() and src_fallback.is_dir():
        return str(src_fallback)

    msg = "Could not resolve package directory. Ensure PACKAGE_DIR, DEV_SRC_PATH, DOCKER_SRC_PATH, or DEFAULT_SRC_DIR is set and points to a valid Python package."
    raise ValueError(msg)


class PathsConfig(BaseModel):
    workspace_root: Path = Field(default_factory=Path.cwd)
    documents_dir: Path = Field(default_factory=lambda: Path.cwd() / "dev_documents")
    package_dir: str = Field(default_factory=_detect_package_dir)
    contracts_dir: str = ""
    artifacts_dir: Path = Field(default_factory=lambda: Path.cwd() / "dev_documents" / "artifacts")
    sessions_dir: str = ".jules/sessions"
    src: Path = Field(default_factory=lambda: Path.cwd() / "src")
    tests: Path = Field(default_factory=lambda: Path.cwd() / "tests")
    templates: Path = Field(default_factory=lambda: Path.cwd() / "dev_documents" / "templates")
    prompts_dir: str = "dev_src/src/prompts"

    @model_validator(mode="after")
    def _set_dependent_paths(self) -> "PathsConfig":
        if not self.contracts_dir:
            self.contracts_dir = f"{self.package_dir}/contracts"
        return self


class JulesConfig(BaseModel):
    executable: str = "jules"
    timeout_seconds: int = Field(
        default_factory=lambda: int(os.getenv("JULES_TIMEOUT_SECONDS", "7200"))
    )
    content_type: str = Field(
        default_factory=lambda: os.getenv("JULES_CONTENT_TYPE", "application/json")
    )
    success_state: str = Field(
        default_factory=lambda: os.getenv("JULES_SUCCESS_STATE", "COMPLETED")
    )
    failure_state: str = Field(default_factory=lambda: os.getenv("JULES_FAILURE_STATE", "FAILED"))
    activities_path: str = Field(
        default_factory=lambda: os.getenv("JULES_ACTIVITIES_PATH", "activities")
    )
    send_message_action: str = Field(
        default_factory=lambda: os.getenv("JULES_SEND_MESSAGE_ACTION", ":sendMessage")
    )
    pr_creation_template: str = Field(
        default_factory=lambda: os.getenv("JULES_PR_CREATION_TEMPLATE", "PR_CREATION_REQUEST.md")
    )
    plan_generated_activity: str = Field(
        default_factory=lambda: os.getenv("JULES_PLAN_GENERATED_ACTIVITY", "planGenerated")
    )
    master_integrator_prefix: str = Field(
        default_factory=lambda: os.getenv("JULES_MASTER_INTEGRATOR_PREFIX", "master-integrator-")
    )
    progress_update_interval: int = Field(
        default_factory=lambda: int(os.getenv("JULES_PROGRESS_UPDATE_INTERVAL", "30"))
    )
    activity_polling_timeout: int = Field(
        default_factory=lambda: int(os.getenv("JULES_ACTIVITY_POLLING_TIMEOUT", "600"))
    )
    polling_interval_seconds: int = Field(
        default_factory=lambda: int(os.getenv("JULES_POLL_INTERVAL_SECONDS", "120"))
    )
    base_url: str = Field(
        default_factory=lambda: os.getenv("JULES_BASE_URL", "https://jules.googleapis.com/v1alpha")
    )
    wait_for_pr_timeout_seconds: int = Field(
        default_factory=lambda: int(os.getenv("JULES_WAIT_FOR_PR_TIMEOUT_SECONDS", "900"))
    )
    max_plan_rejections: int = Field(
        default_factory=lambda: int(os.getenv("JULES_MAX_PLAN_REJECTIONS", "2"))
    )
    request_timeout: float = Field(
        default_factory=lambda: float(os.getenv("JULES_REQUEST_TIMEOUT", "30.0"))
    )
    page_size: int = Field(default_factory=lambda: int(os.getenv("JULES_PAGE_SIZE", "100")))

    # LangGraph session monitoring
    monitor_batch_size: int = Field(
        default_factory=lambda: int(os.getenv("JULES_MONITOR_BATCH_SIZE", "1")),
        description="Number of polls per LangGraph node invocation (batch_size * monitor_poll_interval_seconds = seconds per step).",
    )
    monitor_poll_interval_seconds: int = Field(
        default_factory=lambda: int(os.getenv("JULES_MONITOR_POLL_INTERVAL_SECONDS", "30")),
        description="Seconds between each poll within a monitor batch.",
    )
    stale_session_timeout_seconds: int = Field(
        default_factory=lambda: int(os.getenv("JULES_STALE_SESSION_TIMEOUT_SECONDS", "1800")),
        description=(
            "Seconds without a Jules state change before sending a nudge message. "
            "Jules sometimes enters a silent mode where IN_PROGRESS stays unchanged. "
            "After this many seconds a 'please wrap up and create a PR' prompt is sent. "
            "Default: 1800 (30 minutes)."
        ),
    )
    max_stale_nudges: int = Field(
        default_factory=lambda: int(os.getenv("JULES_MAX_STALE_NUDGES", "3")),
        description="Maximum number of nudge messages to send before giving up and raising a timeout.",
    )

    # Distress detection keywords - Jules sometimes completes but signals a problem in its last message
    distress_keywords: list[str] = Field(
        default_factory=lambda: os.getenv(
            "JULES_DISTRESS_KEYWORDS",
            "inconsistent,cannot act,faulty audit,incorrect version,please manually,blocked,issue with,reiterate,cannot proceed,unable to complete,needs your input",
        ).split(","),
        description=(
            "Keywords in Jules' last agentMessaged activity that indicate it is stuck or "
            "needs help. NOTE: keep these specific - broad words like 'error' will fire on "
            "normal progress messages such as '3 errors were fixed'."
        ),
    )


class ToolsConfig(BaseModel):
    jules_cmd: str = "jules"
    gh_cmd: str = "gh"
    git_cmd: str = "git"
    audit_cmd: str = "bandit"
    uv_cmd: str = "uv"
    mypy_cmd: str = "mypy"
    ruff_cmd: str = "ruff"
    gemini_cmd: str = "gemini"
    required_executables: list[str] = ["uv", "git"]
    conflict_codes: set[str] = Field(
        default_factory=lambda: {"DD", "AU", "UD", "UA", "DU", "AA", "UU"}
    )


class UATConfig(BaseModel):
    playwright_args: list[str] = Field(
        default_factory=lambda: [
            "--browser=chromium",
            "--tracing=on",
            f"-c={Path.cwd() / 'pyproject.toml'}",
            f"--confcutdir={Path.cwd()}",
            f"--rootdir={Path.cwd()}",
        ]
    )


class SandboxConfig(BaseModel):
    """Configuration for E2B Sandbox execution"""

    template: str | None = None
    timeout: int = 7200
    cwd: str = "/home/user/project"
    test_cmd: str = "uv run pytest -v --tb=short"
    max_retries: int = 3
    command_whitelist: list[str] = ["pytest", "uv run pytest", "uv run pytest -v --tb=short"]
    dirs_to_sync: list[str] = ["src", "tests", "contracts", "dev_documents", "dev_src"]
    sandbox_env_cleanup: list[str] = ["UV_PROJECT_ENVIRONMENT"]
    files_to_sync: list[str] = [
        "pyproject.toml",
        "uv.lock",
        ".auditignore",
        "README.md",
    ]
    allowed_cwd_prefixes: list[str] = Field(
        default_factory=lambda: os.getenv("SANDBOX_ALLOWED_CWD_PREFIXES", "/home/,/opt/").split(",")
    )
    install_cmd: str = "pip install --no-cache-dir ruff"
    lint_check_cmd: list[str] = ["uv", "run", "ruff", "check", "--fix", "."]
    type_check_cmd: list[str] = ["uv", "run", "mypy", "src/"]
    security_check_cmd: list[str] = ["uv", "run", "bandit", "-r", "src/", "-ll"]


class ASTAnalyzerConfig(BaseModel):
    max_files: int = Field(default=10000, description="Maximum number of files to analyze")
    max_depth: int = Field(default=20, description="Maximum directory depth to search")
    max_file_size_bytes: int = Field(
        default_factory=lambda: int(os.getenv("AST_ANALYZER_MAX_FILE_SIZE_BYTES", "10485760")),
        description="Maximum file size to read (10MB default)",
    )


class AgentsConfig(BaseSettings):
    auditor_model: str = Field(
        default="openai:gpt-4o",
        alias="AC_CDD_AUDITOR_MODEL",
    )
    qa_analyst_model: str = Field(
        default="openai:gpt-4o",
        alias="AC_CDD_QA_ANALYST_MODEL",
    )
    model_config = SettingsConfigDict(env_prefix="", populate_by_name=True, extra="ignore")


class ReviewerConfig(BaseSettings):
    smart_model: str = Field(
        default="openai:gpt-4o",
        alias="AC_CDD_REVIEWER__SMART_MODEL",
        description="Model for editing code (Fixer)",
    )
    fast_model: str = Field(
        default="openai:gpt-4o-mini",
        alias="AC_CDD_REVIEWER__FAST_MODEL",
        description="Model for reading/auditing code",
    )
    master_integrator_temperature: float = Field(
        default_factory=lambda: float(os.getenv("REVIEWER_MASTER_INTEGRATOR_TEMPERATURE", "0.0"))
    )
    model_config = SettingsConfigDict(env_prefix="", populate_by_name=True, extra="ignore")


class SessionConfig(BaseModel):
    """Session-based development configuration."""

    session_id: str | None = None
    integration_branch_prefix: str = "dev"
    auto_merge_to_integration: bool = True
    final_merge_strategy: Literal["merge", "squash", "rebase"] = "squash"
    auto_delete_session_branches: bool = True


class Settings(BaseSettings):
    """
    Application settings, loaded from environment variables.
    """

    JULES_API_KEY: SecretStr = Field(
        default_factory=lambda: SecretStr(os.getenv("JULES_API_KEY", "")),
        description="Google API key",
    )
    OPENROUTER_API_KEY: SecretStr = Field(
        default_factory=lambda: SecretStr(os.getenv("OPENROUTER_API_KEY", "")),
        description="OpenRouter API key",
    )
    E2B_API_KEY: SecretStr = Field(
        default_factory=lambda: SecretStr(os.getenv("E2B_API_KEY", "")),
        description="E2B Sandbox API key",
    )
    MAX_RETRIES: int = 10
    GRAPH_RECURSION_LIMIT: int = Field(
        default_factory=lambda: int(os.getenv("GRAPH_RECURSION_LIMIT", "2000"))
    )
    DUMMY_CYCLE_ID: str = "00"

    DEFAULT_BASE_BRANCH: str = Field(
        default_factory=lambda: os.getenv("DEFAULT_BASE_BRANCH", "main")
    )
    GCP_PROJECT_ID: str | None = None
    GCP_REGION: str = "us-central1"

    ARCHIVE_DIR_TEMPLATE: str = "system_prompts_phase{phase_num:02d}"
    ARCHIVE_COMMIT_MESSAGE: str = "Archive Phase {phase_num} Artifacts"

    NUM_AUDITORS: int = 3
    REVIEWS_PER_AUDITOR: int = 2
    MAX_ITERATIONS: int = 3

    filename_spec: str = "ALL_SPEC.md"
    filename_arch: str = "SYSTEM_ARCHITECTURE.md"
    max_audit_retries: int = 2

    # Graph Node Names
    required_env_vars: list[str] = ["JULES_API_KEY", "E2B_API_KEY"]
    known_implicit_secrets: list[str] = [
        "DATABASE_URL",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "E2B_API_KEY",
        "JULES_API_KEY",
        "OPENROUTER_API_KEY",
    ]
    default_cycles: list[str] = ["01", "02", "03", "04", "05"]
    architect_context_files: list[str] = [
        "ALL_SPEC.md",
        "SPEC.md",
        "UAT.md",
        "ARCHITECT_INSTRUCTION.md",
    ]

    session: SessionConfig = Field(default_factory=SessionConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    jules: JulesConfig = Field(default_factory=JulesConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    uat: UATConfig = Field(default_factory=UATConfig)
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)
    agents: AgentsConfig = Field(default_factory=AgentsConfig)
    reviewer: ReviewerConfig = Field(default_factory=ReviewerConfig)
    ast_analyzer: ASTAnalyzerConfig = Field(default_factory=ASTAnalyzerConfig)
    tracing: LangSmithConfig = Field(default_factory=LangSmithConfig)

    @property
    def tracing_service(self) -> "Any":
        from src.services.tracing import TracingService

        return TracingService(self.tracing)

    # Graph Node Names
    node_uat_evaluate: str = "uat_evaluate"
    node_sandbox_evaluate: str = "sandbox_evaluate"
    node_coder_critic: str = "coder_critic"

    # Auditor model selection: "smart" or "fast"
    AUDITOR_MODEL_MODE: Literal["smart", "fast"] = Field(default="fast", alias="AUDITOR_MODEL_MODE")

    test_mode: bool = Field(
        default=False,
        alias="TEST_MODE",
        description="Run in test mode with dummy keys and responses",
    )
    auto_approve: bool = Field(
        default=False, alias="AUTO_APPROVE", description="Auto approve AI decisions"
    )

    @model_validator(mode="before")
    @classmethod
    def _parse_booleans(cls, values: Any) -> Any:
        if isinstance(values.get("TEST_MODE"), str):
            values["TEST_MODE"] = values["TEST_MODE"].lower() == "true"
        if isinstance(values.get("AUTO_APPROVE"), str):
            values["AUTO_APPROVE"] = values["AUTO_APPROVE"].lower() == "true"
        return values

    model_config = SettingsConfigDict(
        env_prefix="AC_CDD_",
        env_nested_delimiter="__",
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @model_validator(mode="after")
    def validate_api_keys(self) -> "Settings":
        import os

        missing = []
        if not getattr(self, "test_mode", False):
            if not self.JULES_API_KEY:
                missing.append("JULES_API_KEY")
            if not self.E2B_API_KEY:
                missing.append("E2B_API_KEY")
            if not self.OPENROUTER_API_KEY:
                missing.append("OPENROUTER_API_KEY")

        if missing and not os.environ.get("PYTEST_CURRENT_TEST"):
            # Fallback to test_mode to not break initialization sequence during test runs where test_mode=True is set after instantiation or via kwargs
            msg = f"Missing required environment variables: {', '.join(missing)}"
            raise ValueError(msg)

        # Validate LangSmith Tracing Configuration
        tracing_enabled = self.tracing.tracing_enabled
        api_key = self.tracing.api_key

        if tracing_enabled and not api_key:
            logging.warning(
                "LangSmith tracing enabled but no API key provided. "
                "Tracing will be ignored to prevent crashes."
            )
            os.environ["LANGCHAIN_TRACING_V2"] = "false"
            self.tracing.tracing_enabled = False

        return self

    @property
    def current_session_id(self) -> str:
        """Get or generate session ID."""
        if self.session.session_id:
            return self.session.session_id
        now = datetime.now(UTC)
        return f"session-{now.strftime('%Y%m%d-%H%M%S-%f')[:20]}"

    @property
    def integration_branch(self) -> str:
        return f"{self.session.integration_branch_prefix}/{self.current_session_id}/integration"

    def get_template(self, name: str) -> Path:
        """Resolve a template path."""
        user_path = self.paths.documents_dir / "system_prompts" / name
        if user_path.exists():
            return user_path

        package_template_path = Path(__file__).parent / "templates" / name
        if package_template_path.exists():
            return package_template_path

        return user_path

    def get_prompt_content(self, filename: str, default: str = "") -> str:
        """Reads prompt content."""
        target_filename = PROMPT_FILENAME_MAP.get(filename, filename)
        path = self.get_template(target_filename)

        if path.exists():
            return path.read_text(encoding="utf-8").strip()

        fallback_path = Path(self.paths.prompts_dir) / filename
        if fallback_path.exists():
            return fallback_path.read_text(encoding="utf-8").strip()

        return default

    def get_context_files(self) -> list[str]:
        p = self.paths.documents_dir
        if not p.exists():
            p = Path.cwd() / "dev_documents"

        # explicit file list to include all vital architectural and testing context
        target_files = [
            self.filename_spec,
            self.filename_arch,
            "SPEC.md",
            "UAT.md",
            "USER_TEST_SCENARIO.md",
        ]

        found_files = []
        for fname in target_files:
            fpath = p / fname
            if fpath.exists() and str(fpath) not in found_files:
                found_files.append(str(fpath))

        if found_files:
            return found_files

        # Fallback: if main spec missing, include all MDs (legacy behavior)
        if p.exists():
            return [str(f) for f in p.glob("*.md")]
        return []

    def get_target_files(self) -> list[str]:
        targets = []
        src = self.paths.src
        if not src.exists():
            src = Path.cwd() / "src"

        tests = self.paths.tests
        if not tests.exists():
            tests = Path.cwd() / "tests"

        if src.exists():
            targets.extend([str(p) for p in src.rglob("*.py")])
        if tests.exists():
            targets.extend([str(p) for p in tests.rglob("*.py")])

        # Include pyproject.toml if it exists (for dependencies)
        pyproject = Path.cwd() / "pyproject.toml"
        if pyproject.exists():
            targets.append(str(pyproject))

        return targets


# Global settings object
settings = Settings()
