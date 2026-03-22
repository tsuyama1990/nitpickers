# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo>=0.21.1",
#     "pydantic~=2.11.0",
#     "python-dotenv~=1.0.1",
#     "litellm~=1.60.2"
# ]
# ///
import marimo

__generated_with = "0.21.1"
app = marimo.App()

@app.cell
def _step_1() -> tuple[object, object]:
    import marimo as mo

    intro = mo.md(
        """
        # NITPICKERS: End-to-End Automated UAT Pipeline (Real Mode)

        This interactive tutorial demonstrates the fully automated, multi-modal User Acceptance Testing (UAT) pipeline of the NITPICKERS framework.
        It operates strictly in **Real Mode** using actual API keys to interface with external LLM providers and Git environments, guaranteeing no mocked behavior.
        """
    )
    return intro, mo

@app.cell
def _step_2() -> tuple[object, object, object, object, object]:
    import os
    import sys
    from pathlib import Path

    import dotenv

    # Ensure src package is importable
    repo_root = Path.cwd()
    if str(repo_root) not in sys.path:
        sys.path.append(str(repo_root))

    # Load environment variables
    dotenv.load_dotenv(repo_root / ".env")

    # Assert necessary API keys are present (Do not print them!)
    assert os.getenv("OPENROUTER_API_KEY"), "OPENROUTER_API_KEY is missing"
    assert os.getenv("JULES_API_KEY"), "JULES_API_KEY is missing"
    assert os.getenv("E2B_API_KEY"), "E2B_API_KEY is missing"
    assert os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN"), "GITHUB_PERSONAL_ACCESS_TOKEN is missing"

    # Ensure LangSmith Tracing is natively configured for tutorials
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = "nitpickers-live-tutorial"
    if "LANGSMITH_API_KEY" in os.environ:
        os.environ["LANGCHAIN_API_KEY"] = os.environ["LANGSMITH_API_KEY"]

    # Important: Turn OFF mock LLM behavior globally
    os.environ["MOCK_LLM"] = "false"

    return os, sys, Path, dotenv, repo_root

@app.cell
def _step_3(mo, repo_root): # type: ignore[no-untyped-def]
    import asyncio

    from src.config import settings
    from src.domain_models import FixPlanSchema, UatExecutionState
    from src.services.auditor_usecase import UATAuditorUseCase
    from src.services.llm_reviewer import LLMReviewer
    from src.state import CycleState

    mo.md("## Live UAT Auditor Diagnosis Execution")

    async def execute_live_diagnosis() -> dict[str, object]:
        # Instantiate real dependencies
        llm_reviewer = LLMReviewer()
        uat_auditor = UATAuditorUseCase(llm_reviewer=llm_reviewer)

        # Create a genuine failed execution state to diagnose
        uat_state = UatExecutionState(
            exit_code=1,
            stdout="Running End-to-End User Acceptance Tests...\n",
            stderr="AssertionError: Expected element '#submit-button' to be visible, but it was not found in the DOM.",
            artifacts=[],
        )

        state = CycleState(cycle_id="01")
        state.project_session_id = "live-tutorial-session"
        state.uat_execution_state = uat_state

        # Execute the real agentic LLM review
        return await uat_auditor.execute(state)

    return (
        execute_live_diagnosis,
        asyncio,
        settings,
        FixPlanSchema,
        UatExecutionState,
        UATAuditorUseCase,
        LLMReviewer,
        CycleState,
    )


@app.cell
async def _step_4(execute_live_diagnosis, mo): # type: ignore[no-untyped-def]
    # Run the live diagnosis
    try:
        # We handle asyncio execution natively for marimo context
        result = await execute_live_diagnosis()
        status = "Success"
        fix_plan = result["current_fix_plan"]
    except Exception as e:
        status = f"Failed: {e!s}"
        result = None
        fix_plan = None

    display = [mo.md(f"### Execution Status: `{status}`")]

    if fix_plan:
        display.append(mo.md(f"#### Diagnosed Defect:\n{fix_plan.defect_description}"))
        if fix_plan.patches:
            patch = fix_plan.patches[0]
            display.append(mo.md(f"#### Proposed Target File:\n`{patch.target_file}`"))
            display.append(mo.md(f"#### Live Generated Patch:\n```\n{patch.git_diff_patch}\n```"))

    mo.vstack(display)
    return result, status, fix_plan, display

if __name__ == "__main__":
    app.run()
