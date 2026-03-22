import re
from collections.abc import Generator
from typing import Any

import pytest

from src.config import settings
from src.domain_models import MultiModalArtifact


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, Any, None]:
    """Capture Playwright screenshot and DOM state on test failure."""
    # Execute all other hooks to obtain the report object
    outcome = yield
    report = outcome.get_result()

    # We only care about actual failing test calls, not setup/teardown
    if report.when == "call" and report.failed and "page" in getattr(item, "fixturenames", []):
        page = getattr(item, "funcargs", {}).get("page")
        if page:
            # Ensure artifacts directory exists
            artifacts_dir = settings.paths.artifacts_dir
            artifacts_dir.mkdir(parents=True, exist_ok=True)

            # Create a safe filename based on the test nodeid
            safe_name = re.sub(r"[^\w\-_\.]", "_", item.nodeid)
            screenshot_path = artifacts_dir / f"{safe_name}.png"
            trace_path = artifacts_dir / f"{safe_name}_trace.zip"

            # Extract console logs if they were captured by the test
            # The developer must attach console messages to the page context,
            # but we will look for a custom `console_logs` list on the page fixture.
            console_logs = getattr(page, "console_logs", [])

            try:
                # Capture full-page screenshot
                page.screenshot(path=str(screenshot_path), full_page=True, timeout=5000)

                # Capture DOM / Accessibility Tree for the LLM
                dom_snapshot_path = artifacts_dir / f"{safe_name}_dom.txt"
                try:
                    # The Accessibility tree is heavily compressed and perfect for LLMs
                    a11y_snapshot = page.accessibility.snapshot()
                    import json

                    dom_snapshot_path.write_text(json.dumps(a11y_snapshot, indent=2))
                except Exception as dom_err:
                    dom_snapshot_path.write_text(f"DOM Capture Failed: {dom_err}")

                # Stop tracing and export
                if hasattr(page.context, "tracing"):
                    page.context.tracing.stop(path=str(trace_path))
                else:
                    # If tracing wasn't started, create an empty trace file for validation
                    trace_path.write_bytes(b"")

            except Exception as e:
                # If Playwright fails to capture, log it but don't break the test run
                console_logs.append(f"Failed to capture artifact: {e}")
                # Ensure dummy files exist to satisfy validation if capture completely failed
                if not screenshot_path.exists():
                    screenshot_path.write_bytes(b"")
                if not trace_path.exists():
                    trace_path.write_bytes(b"")

            # Create and validate the multi-modal artifact schema
            artifact = MultiModalArtifact(
                test_id=item.nodeid,
                screenshot_path=str(screenshot_path),
                trace_path=str(trace_path),
                console_logs=console_logs,
                traceback=report.longreprtext or "",
            )

            # Attach the artifact to the report
            report.multimodal_artifact = artifact


@pytest.fixture(autouse=True)
def _inject_dummy_keys(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest) -> None:
    """Set dummy API keys and models before any tests run, to prevent pydantic-ai from complaining
    during module import and inspection without leaking to the global environment."""
    if "live" in request.node.keywords:
        return

    import uuid

    # Set random strings for mock validation so no credentials can be leaked.
    monkeypatch.setenv("OPENAI_API_KEY", f"sk-test-{uuid.uuid4().hex}")
    monkeypatch.setenv("ANTHROPIC_API_KEY", f"sk-test-{uuid.uuid4().hex}")
    monkeypatch.setenv("GEMINI_API_KEY", f"sk-test-{uuid.uuid4().hex}")
    monkeypatch.setenv("OPENROUTER_API_KEY", f"sk-test-{uuid.uuid4().hex}")
    monkeypatch.setenv("JULES_API_KEY", f"sk-test-{uuid.uuid4().hex}")
    monkeypatch.setenv("E2B_API_KEY", f"e2b-test-{uuid.uuid4().hex}")

    monkeypatch.setenv("NITPICK_AUDITOR_MODEL", "openai:gpt-4o")
    monkeypatch.setenv("NITPICK_QA_ANALYST_MODEL", "openai:gpt-4o")
    monkeypatch.setenv("NITPICK_REVIEWER__SMART_MODEL", "openai:gpt-4o")
    monkeypatch.setenv("NITPICK_REVIEWER__FAST_MODEL", "openai:gpt-3.5-turbo")
