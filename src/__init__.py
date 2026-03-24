import sys
import pydantic
import pydantic.fields

# HOTFIX: Bypass LangChain's broken pydantic.v1 imports with Pydantic 2.10+
# Map the removed v1 namespace directly to Pydantic V2
sys.modules["pydantic.v1"] = pydantic
sys.modules["pydantic.v1.fields"] = pydantic.fields
