PYTHON=python
UVICORN=uvicorn
SCHEMATHESIS=schemathesis

.PHONY: lint typecheck test contract load run release-checklist

lint:
\truff check api tests

typecheck:
\tpyright

test:
\tpytest

contract:
\t$(SCHEMATHESIS) run docs/openapi/v1.yaml --base-url http://localhost:8000

load:
\t@echo "Run k6 load test via scripts/load-test.js"

run:
\t$(UVICORN) api.app.main:app --host 0.0.0.0 --port 8000

release-checklist:
\tpwsh -File scripts/build-release-checklist.ps1 -ServiceName golden-service-python -ReleaseTag dev

check: lint typecheck test
