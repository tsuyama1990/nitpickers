import json
import uuid
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from langchain_core.runnables import RunnableConfig
from src.services.workflow import WorkflowService
from src.services.rca_service import RCAService
from src.utils import current_trace_id, TraceIdCallbackHandler, sync_context_from_config, current_cycle_id
from src.state import CycleState

from types import SimpleNamespace

@pytest.mark.asyncio
async def test_trace_id_callback_handler():
    """Verify that TraceIdCallbackHandler correctly updates current_trace_id."""
    handler = TraceIdCallbackHandler()
    test_run_id = uuid.uuid4()
    
    # Reset context
    current_trace_id.set("N/A")
    
    # Simulate chain start
    handler.on_chain_start({}, {}, run_id=test_run_id)
    assert current_trace_id.get() == str(test_run_id)
    
    # Simulate node start with config restoration
    new_run_id = uuid.uuid4()
    # Use SimpleNamespace for deterministic property/dict access that bypasses MagicMock's greedy return-moking
    config = SimpleNamespace(
        run_id=new_run_id,
        configurable={"cycle_id": "99"}
    )
    
    handler.on_node_start({}, {}, config=config)
    assert current_trace_id.get() == str(new_run_id)
    assert current_cycle_id.get() == "99"

@pytest.mark.asyncio
async def test_state_optimization_truncation():
    """Verify that WorkflowService correctly truncates state for LLM payloads."""
    # Mock GraphBuilder to avoid real SandboxRunner validation
    with patch("src.services.workflow.GraphBuilder"):
        service = WorkflowService(services=MagicMock())
        
        # Use a dict to avoid Pydantic validation overhead/errors in unit test
        state = {
            "cycle_id": "01",
            "session": {
                "messages": [{"role": "user", "content": "msg"}] * 20
            }
        }
        
        optimized = service._get_llm_optimized_state(state)
        
        # Should be truncated to 10
        assert len(optimized["session"]["messages"]) == 10
        assert optimized["session"]["_truncated"] is True

@pytest.mark.asyncio
async def test_rca_sanitization():
    """Verify that RCAService sanitizes sensitive info before LLM calls."""
    rca = RCAService(model="gpt-4o-mini")
    
    # Snapshot containing a standard format API key
    snapshot = {
        "error": "Failed with key sk-ant-api-012345678901234567890123456789", # 35 chars after sk-
        "trace_id": "test-trace",
    }
    # Log containing a password
    log_tail = "Connecting with pass: MySecretPassword123"
    
    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value.choices = [MagicMock(message=MagicMock(content="Analysis"))]
        
        await rca._call_rca_llm("01", snapshot, log_tail)
        
        # Check the prompt sent to LLM
        call_args = mock_complete.call_args
        prompt_content = call_args[1]["messages"][1]["content"]
        
        # Sensitive data should be redacted
        assert "MySecretPassword123" not in prompt_content
        assert "sk-ant-api-01" not in prompt_content
        assert "[REDACTED" in prompt_content

@pytest.mark.asyncio
async def test_workflow_background_tasks():
    """Verify that WorkflowService manages background tasks correctly to avoid gc issues."""
    with patch("src.services.workflow.GraphBuilder"):
        service = WorkflowService(services=MagicMock())
        
        # Mock RCAService at its source module so that local imports pick it up
        with patch("src.services.rca_service.RCAService") as mock_rca_cls:
            mock_rca = mock_rca_cls.return_value
            mock_rca.analyze_failure = AsyncMock()
            
            # Add a task via _save_failure_snapshot
            await service._save_failure_snapshot("01", {}, "error")
            
            # Verify task is in set
            assert len(service._background_tasks) == 1
            
            # Wait for task to complete
            task = list(service._background_tasks)[0]
            await task
            
            # Verify task is removed from set via done_callback
            assert len(service._background_tasks) == 0

@pytest.mark.asyncio
async def test_resilient_logging():
    """Verify that ResilientRichHandler handles missing cycle_id without crashing."""
    from src.utils import ResilientRichHandler
    import logging
    
    # Create a record without cycle_id
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname=__file__, lineno=1,
        msg="Test message", args=(), exc_info=None
    )
    
    handler = ResilientRichHandler()
    # This should not raise KeyError
    handler.emit(record)
    
    assert hasattr(record, "cycle_id")
    assert record.cycle_id == "CORE" # Default value
