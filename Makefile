run:
	python -m app.bot

webhook:
	python -m app.bot --webhook

lint:
	python -m compileall -q app test_setup.py

env:
	cp env.example .env || true

install:
	pip install -r requirements.txt

clean:
	rm -rf data/*.txt data/*.m4a data/*.mp3 data/*.mp4 data/*.webm data/*.vtt data/*.srt \
		__pycache__ app/__pycache__

test:
	python test_setup.py

.PHONY: run webhook lint env install clean test
