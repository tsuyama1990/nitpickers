with open("tests/uat/verify_cycle_01_planning.py", "r") as f:
    content = f.read()

content = content.replace("def test_architect_critic_response_schema():", "def test_architect_critic_response_schema() -> None:")

with open("tests/uat/verify_cycle_01_planning.py", "w") as f:
    f.write(content)

with open("dev_src/ac_cdd_core/interfaces.py", "r") as f:
    content = f.read()

if "architect_critic_node" not in content:
    content = content.replace("async def architect_session_node(self, state: CycleState) -> dict[str, Any]: ...", "async def architect_session_node(self, state: CycleState) -> dict[str, Any]: ...\n    async def architect_critic_node(self, state: CycleState) -> dict[str, Any]: ...")
    with open("dev_src/ac_cdd_core/interfaces.py", "w") as f:
        f.write(content)
