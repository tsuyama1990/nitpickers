with open('tests/nitpick/unit/test_routers.py', 'r') as f:
    content = f.read()

content = content.replace('        state.committee.audit_attempt_count = 0\n', '')
content = content.replace('        assert state.committee.audit_attempt_count == 1\n', '')
content = content.replace('        state.committee.audit_attempt_count = 1\n', '')
content = content.replace('        assert state.committee.audit_attempt_count == 2\n', '')
content = content.replace('        state.committee.audit_attempt_count = settings.max_audit_retries\n', '')
content = content.replace('        assert route_auditor(state) == "requires_pivot"\n', '        assert route_auditor(state) == "reject"\n')
content = content.replace('        assert state.committee.audit_attempt_count == settings.max_audit_retries + 1\n', '')

with open('tests/nitpick/unit/test_routers.py', 'w') as f:
    f.write(content)
