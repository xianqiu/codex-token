PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

.PHONY: install test smoke smoke-project smoke-session

install:
	$(PIP) install -e .

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v

smoke:
	codex-token summary

smoke-project:
	codex-token project $(PWD)

smoke-session:
	codex-token session 019cf082 --events 3
