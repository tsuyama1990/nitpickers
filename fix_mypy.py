import re

# fix tests/ac_cdd/unit/test_coder_critic_flow.py
with open("tests/ac_cdd/unit/test_coder_critic_flow.py", "r") as f:
    c = f.read()
c = re.sub(r"def (\w+)\(.*\) -> Any:", lambda m: f"def {m.group(1)}({m.group(0).split('(')[1].split(')')[0]}) -> None:", c)
c = c.replace("Generator", "Any")
with open("tests/ac_cdd/unit/test_coder_critic_flow.py", "w") as f:
    f.write(c)

# fix dev_src/ac_cdd_core/services/jules_client.py
with open("dev_src/ac_cdd_core/services/jules_client.py", "r") as f:
    c = f.read()
c = c.replace("credentials: Credentials = None", "credentials: Any = None")
c = c.replace("google.auth.default()  # type: ignore[no-untyped-call]", "google.auth.default()  # type: ignore")
with open("dev_src/ac_cdd_core/services/jules_client.py", "w") as f:
    f.write(c)

# fix tests/ac_cdd/unit/test_architect_critic.py
with open("tests/ac_cdd/unit/test_architect_critic.py", "r") as f:
    c = f.read()
c = c.replace("def mock_jules_client() -> AsyncMock:", "def mock_jules_client() -> Any:")
c = c.replace("def cycle_nodes(mock_jules_client: AsyncMock) -> CycleNodes:", "def cycle_nodes(mock_jules_client: Any) -> Any:")
c = c.replace("async def test_architect_critic_node_rejected(cycle_nodes: CycleNodes, mock_jules_client: AsyncMock) -> None:", "async def test_architect_critic_node_rejected(cycle_nodes: Any, mock_jules_client: Any) -> None:")
c = c.replace("async def test_architect_critic_node_approved(cycle_nodes: CycleNodes, mock_jules_client: AsyncMock) -> None:", "async def test_architect_critic_node_approved(cycle_nodes: Any, mock_jules_client: Any) -> None:")
with open("tests/ac_cdd/unit/test_architect_critic.py", "w") as f:
    f.write(c)
