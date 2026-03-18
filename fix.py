with open("src/services/workflow.py", "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "mgr.update_project_state(" in line:
        lines[i] = line.replace("mgr.update_project_state(", "mgr.update_project_state(")

with open("src/services/workflow.py", "w") as f:
    f.writelines(lines)
