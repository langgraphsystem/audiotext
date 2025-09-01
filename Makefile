run:
	python -m app.bot

lint:
	rufflehog || true

env:
	cp env.example .env || true

install:
	pip install -r requirements.txt

clean:
	rm -rf data/*.txt data/*.m4a data/*.mp3 __pycache__ app/__pycache__

test:
	python test_setup.py

.PHONY: run lint env install clean test
