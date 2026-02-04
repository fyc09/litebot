SHELL := /bin/bash

FRONTEND_SRC := $(shell find frontend/src -type f) frontend/index.html frontend/vite.config.js frontend/package.json
FRONTEND_STAMP := iribot/static/.built

.PHONY: build frontend package clean install uninstall

build: frontend package

frontend: $(FRONTEND_STAMP)

$(FRONTEND_STAMP): $(FRONTEND_SRC)
	cd frontend && npm install && npm run build
	rm -rf iribot/static
	mkdir -p iribot/static
	cp -R frontend/dist/. iribot/static/
	@mkdir -p $(dir $@)
	@touch $@

package:
	python -m pip install --upgrade build twine
	python -m build
	python -m twine check dist/*.whl dist/*.tar.gz

install:
	python -m pip install -e .

uninstall:
	python -m pip uninstall -y iribot

clean:
	rm -rf dist build *.egg-info iribot/static
