VENV ?= .venv
PY   ?= $(VENV)/bin/python
PIP  ?= $(VENV)/bin/pip

# Полная подготовка к первому запуску
setup: venv install env
	@echo ""
	@echo "Готово. Заполните .env (BOT_TOKEN, OPENAI_API_KEY) и запустите: make run"

venv:
	python3 -m venv $(VENV)

install:
	$(PIP) install -q -r requirements.txt

env:
	@test -f .env || cp env.example .env

run:
	$(PY) -m app.bot

webhook:
	$(PY) -m app.bot --webhook

test:
	$(PY) test_setup.py

lint:
	$(PY) -m compileall -q app test_setup.py

# Запуск в Docker: FFmpeg и зависимости уже в образе
docker-up:
	docker compose up --build

docker-down:
	docker compose down

clean:
	rm -rf data/*.txt data/*.m4a data/*.mp3 data/*.mp4 data/*.webm data/*.vtt data/*.srt \
		data/*.jpg __pycache__ app/__pycache__

.PHONY: setup venv install env run webhook test lint docker-up docker-down clean
