import base64
from typing import Any

import anyio
import litellm
from pydantic import ValidationError

from src.domain_models import AuditorReport, FixPlanSchema, UatExecutionState
from src.utils import logger


class LLMReviewer:
    """
    Direct LLM Client for conducting static code reviews.
    Uses litellm to communicate with various LLM providers (OpenRouter, Gemini, etc.).
    """

    def __init__(self, sandbox_runner: object | None = None) -> None:
        # sandbox_runner is accepted for dependency injection compatibility
        # even if not strictly used by this class (files are passed as content)
        self.sandbox = sandbox_runner

        import os

        # Enable LangSmith supervision natively through litellm if configured
        if os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true":
            litellm.success_callback = ["langsmith"]

        # We rely on litellm's environment variable handling for API keys.
        # Ensure litellm is verbose enough for debugging if needed, but keep logs clean by default.
        litellm.suppress_instrumentation = True

    async def _validate_paths(
        self, target_files: dict[str, str], context_docs: dict[str, str]
    ) -> str | None:
        if not target_files:
            logger.warning("review_code called with empty target_files dictionary.")
            return "-> REVIEW_FAILED\n\n### Critical Issues\n- **Issue**: SYSTEM_ERROR: No target files provided for review.\n  - Location: `Unknown`\n  - Concrete Fix: Ensure files are modified before requesting an audit."

        import pathlib

        import anyio

        cwd = await anyio.Path(pathlib.Path.cwd()).resolve(strict=False)

        async def _is_path_safe(p: str) -> bool:
            if ".." in p:
                return False
            try:
                return (await anyio.Path(p).resolve(strict=False)).is_relative_to(
                    cwd
                ) or p.startswith("/")
            except Exception:
                return False

        invalid_targets = [path for path in target_files if not await _is_path_safe(path)]
        if invalid_targets:
            logger.warning(f"review_code rejecting invalid target file paths: {invalid_targets}")
            return f"-> REVIEW_FAILED\n\n### Critical Issues\n- **Issue**: SYSTEM_ERROR: Invalid target file path detected: {', '.join(invalid_targets)}\n  - Location: `Unknown`\n  - Concrete Fix: Remove path traversal or unsafe characters."

        invalid_contexts = [path for path in context_docs if not await _is_path_safe(path)]
        for path in invalid_contexts:
            logger.warning(f"review_code rejecting invalid context doc path: {path}")
            del context_docs[path]

        return None

    async def review_code(
        self,
        target_files: dict[str, str],
        context_docs: dict[str, str],
        instruction: str,
        model: str,
    ) -> str:
        """
        Sends file contents and instructions to the LLM for review.
        Validates the output strictly against the AuditorReport Pydantic schema.
        """

        validation_error = await self._validate_paths(target_files, context_docs)
        if validation_error:
            return validation_error

        total_files = len(target_files) + len(context_docs)
        logger.info(
            f"LLMReviewer: preparing structured review for {total_files} files using model {model}"
        )

        # specific prompt construction with strict separation
        prompt = self._construct_prompt(target_files, context_docs, instruction)

        # Retry logic (up to 2 retries, total 3 attempts)
        for attempt in range(3):
            try:
                # Add asyncio timeout wrapper for safety against LLM hangs
                with anyio.fail_after(120):
                    response = await litellm.acompletion(
                        model=model,
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "You are an automated code reviewer. You must strictly follow the "
                                    "provided instructions and only review the target code. You MUST return valid JSON. "
                                    "IMPORTANT: Report only the most critical issues. Limit your 'issues' array to a "
                                    "MAXIMUM of 10 issues to prevent excessively large JSON generation."
                                ),
                            },
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.0,  # Deterministic output for reviews
                        max_tokens=8192,  # Prevent generating astronomically huge JSON strings that get truncated
                    )

                content_str = response.choices[0].message.content

                # Parse the response safely into our robust Pydantic model
                report = AuditorReport.model_validate_json(content_str)
                return self._format_as_markdown(report)

            except TimeoutError:
                logger.warning(f"LLMReviewer attempt {attempt + 1} timed out after 120s.")
                if attempt == 2:
                    logger.error("LLMReviewer failed completely due to persistent timeouts.")
                    return "-> REVIEW_FAILED\n\n### Critical Issues\n- **Issue**: SYSTEM_ERROR: LLM Review API timed out.\n  - Location: `Unknown`\n  - Concrete Fix: Try again later or simplify the changes."
            except (ValidationError, Exception) as e:
                logger.warning(f"LLMReviewer attempt {attempt + 1} failed to parse JSON: {e}")
                # Exponential backoff circuit-breaker logic
                await anyio.sleep(2.0 * (attempt + 1))
                if attempt == 2:
                    logger.error("LLMReviewer failed completely after 3 attempts.")
                    return f"-> REVIEW_FAILED\n\n### Critical Issues\n- **Issue**: SYSTEM_ERROR: LLM API generated invalid JSON. ({e})\n  - Location: `Unknown` (Line Unknown)\n  - Concrete Fix: Ensure your changes are simple and try again."

        return "-> REVIEW_FAILED\n\n### Critical Issues\n- **Issue**: SYSTEM_ERROR: Review loop failed unexpectedly\n  - Location: `Unknown`\n  - Concrete Fix: Ensure your changes are simple and try again."

    async def diagnose_uat_failure(  # noqa: C901
        self,
        uat_state: UatExecutionState,
        instruction: str,
        model: str,
    ) -> FixPlanSchema:
        """
        Stateless diagnostic outer loop. Analyzes UAT execution logs and Multi-Modal artifacts
        to provide a highly specific FixPlanSchema.
        """
        logger.info(f"LLMReviewer: starting UAT failure diagnosis using {model}")

        from src.utils_sanitization import sanitize_for_llm

        # Robust sanitization to prevent prompt injection and handle API payloads securely
        safe_stdout = sanitize_for_llm(uat_state.stdout)
        safe_stderr = sanitize_for_llm(uat_state.stderr)
        safe_instruction = sanitize_for_llm(instruction)

        content_parts: list[dict[str, str | dict[str, str]]] = [
            {
                "type": "text",
                "text": f"{safe_instruction}\n\n# Execution Output\n\nExit Code: {uat_state.exit_code}\n\n## Stdout\n```\n{safe_stdout}\n```\n\n## Stderr\n```\n{safe_stderr}\n```\n",
            }
        ]

        # Helper inner function specifically to unpack the parsing block complexity
        async def _append_artifact(a: "Any") -> None:
            if not a.screenshot_path:
                return
            if ".." in a.screenshot_path:
                msg = f"Unsafe artifact path: {a.screenshot_path}"
                raise ValueError(msg)

            img_path = anyio.Path(a.screenshot_path)
            if await img_path.exists() and await img_path.is_file():
                img_data = await img_path.read_bytes()
                encoded = base64.b64encode(img_data).decode("utf-8")
                if not encoded:
                    msg = "Base64 encoding resulted in empty string"
                    raise ValueError(msg)

                content_parts.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{encoded}"},
                    }
                )
                safe_traceback = sanitize_for_llm(a.traceback)
                content_parts.append(
                    {
                        "type": "text",
                        "text": f"\n# Traceback for artifact {a.test_id}\n```\n{safe_traceback}\n```\n",
                    }
                )
            else:
                logger.warning(
                    f"Artifact screenshot not found or is not a file: {a.screenshot_path}"
                )

        # Attach multimodal artifacts
        for artifact in uat_state.artifacts:
            try:
                await _append_artifact(artifact)
            except Exception as e:
                logger.error(f"Failed to process multimodal artifact {artifact.test_id}: {e}")

        for attempt in range(3):
            try:
                # Add asyncio timeout wrapper for safety against LLM hangs
                with anyio.fail_after(120):
                    response = await litellm.acompletion(
                        model=model,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are the Outer Loop Diagnostician. You must strictly output valid JSON matching the FixPlanSchema.",
                            },
                            {"role": "user", "content": content_parts},
                        ],
                        response_format=FixPlanSchema,
                        temperature=0.0,
                        max_tokens=8192,
                    )

                content_str = response.choices[0].message.content
                if not content_str:
                    pass  # We'll just try again, it's inside the loop
                else:
                    return FixPlanSchema.model_validate_json(content_str)
            except TimeoutError:
                logger.warning(f"diagnose_uat_failure attempt {attempt + 1} timed out.")
                await anyio.sleep(2.0 * (attempt + 1))
            except (ValidationError, Exception) as e:
                logger.warning(f"diagnose_uat_failure attempt {attempt + 1} failed: {e}")
                await anyio.sleep(2.0 * (attempt + 1))
                if attempt == 2:
                    logger.error("diagnose_uat_failure failed completely after 3 attempts.")
                    from src.domain_models.fix_plan_schema import FilePatch

                    # Fallback schema to not break the pipeline entirely, though we ideally raise
                    return FixPlanSchema(
                        defect_description=f"SYSTEM_ERROR: LLM API generated invalid JSON or failed. {e}",
                        patches=[
                            FilePatch(
                                target_file="Unknown",
                                git_diff_patch="Please review the UAT logs manually and provide a fix.",
                            )
                        ],
                    )

        # Unreachable but mypy needs it
        from src.domain_models.fix_plan_schema import FilePatch

        return FixPlanSchema(
            defect_description="SYSTEM_ERROR: Review loop failed unexpectedly.",
            patches=[
                FilePatch(
                    target_file="Unknown", git_diff_patch="Please review the UAT logs manually."
                )
            ],
        )

    def _format_as_markdown(self, report: AuditorReport) -> str:
        """Converts the deeply nested AuditorReport Pydantic object into a clean Markdown string for the Coder."""
        feedback = "-> REVIEW_PASSED\n\n" if report.is_passed else "-> REVIEW_FAILED\n\n"

        feedback += f"### Summary\n{report.summary}\n\n"

        if report.issues:
            feedback += "### Critical Issues\n"
            for issue in report.issues:
                feedback += f"- **[{issue.category.upper()}]**: {issue.issue_description}\n"
                feedback += f"  - **Location**: `{issue.file_path}`\n"
                feedback += (
                    f"  - **Target Snippet**:\n    ```\n    {issue.target_code_snippet}\n    ```\n"
                )
                feedback += f"  - **Concrete Fix**: {issue.concrete_fix}\n\n"

        return feedback

    def _construct_prompt(
        self, target_files: dict[str, str], context_docs: dict[str, str], instruction: str
    ) -> str:
        """
        Format the prompt with strict Context/Target separation.
        """

        # 1. Context Section (Specs)
        context_section = ""
        for name, content in context_docs.items():
            context_section += f"\nFile: {name} (READ-ONLY SPECIFICATION)\n```\n{content}\n```\n"

        # 2. Target Section (Code)
        target_section = ""
        for name, content in target_files.items():
            # Add python hint for .py files
            lang = "python" if name.endswith(".py") else ""
            target_section += f"\nFile: {name} (AUDIT TARGET)\n```{lang}\n{content}\n```\n"

        # 3. Assemble Prompt
        return f"""
{instruction}

###################

🚫 READ-ONLY CONTEXT (GROUND TRUTH)

The following files define the specifications.
You must NOT critique, review, or suggest changes to these files.
Use them ONLY as the reference to judge the code.

###################
{context_section}

###################

🎯 AUDIT TARGET (CODE TO REVIEW)

Strictly review the following files against the context above.
Provide feedback ONLY for these files.

###################
{target_section}
"""
