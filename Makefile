VENV_DIR = venv
PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip

# Targets
.PHONY: all venv install run clean distclean

all: venv install run

venv:
	python3 -m venv $(VENV_DIR)

install:
	$(PIP) install -r requirements.txt

run:
	$(PYTHON) main.py

distclean:
	rm -rf $(VENV_DIR)

clean:
	rm -rf results-*
