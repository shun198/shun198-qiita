SHELL := /bin/bash

.PHONY: help setup init login preview pull lint

help:
	@echo "Available targets:"
	@echo "  make setup   - Install dependencies with pnpm"
	@echo "  make init    - Initialize Qiita CLI config"
	@echo "  make login   - Login to Qiita CLI"
	@echo "  make preview - Start Qiita preview server"
	@echo "  make pull    - Pull articles from Qiita"
	@echo "  make lint    - Run markdown and text lint"

setup:
	pnpm install

init:
	pnpm exec qiita init

login:
	pnpm exec qiita login

preview:
	pnpm exec qiita preview

pull:
	pnpm run qiita:pull

lint:
	pnpm run lint
