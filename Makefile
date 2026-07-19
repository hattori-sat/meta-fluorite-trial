SHELL := /bin/bash

.DEFAULT_GOAL := help

.PHONY: help setup setup-project setup-macos setup-build-host \
	check-canonical check-privacy check-shell check-python check-mcp \
	check-markdown check-file-sizes check-staged-whitespace verify ci

help:
	@printf '%s\n' \
		'Fluorite repository development targets' \
		'' \
		'  make setup             Check project prerequisites (no installation)' \
		'  make setup-macos       Check optional macOS/QEMU prerequisites' \
		'  make setup-build-host  Check an AGL build host; requires AGL_ROOT' \
		'  make verify            Run every repository verification gate' \
		'  make check-staged-whitespace  Check the exact staged commit candidate' \
		'  make ci                CI entry point (same gates as verify)'

setup: setup-project

setup-project:
	@bash scripts/setup-project.sh

setup-macos:
	@bash scripts/setup-macos.sh

setup-build-host:
	@bash scripts/setup-build-host.sh

check-canonical:
	@bash scripts/assert-canonical-repository.sh

check-privacy:
	@bash scripts/check-repository-privacy.sh .

check-shell:
	@bash scripts/check-shell-syntax.sh .

check-python:
	@bash scripts/check-python-unittest.sh .

check-mcp:
	@bash scripts/check-mcp-smoke.sh .

check-markdown:
	@bash scripts/check-markdown-links.sh .

check-file-sizes:
	@bash scripts/check-file-sizes.sh .

check-staged-whitespace:
	@bash scripts/check-staged-whitespace.sh

verify: check-canonical check-privacy check-shell check-python check-mcp check-markdown check-file-sizes

ci: verify
