.PHONY: up down build test lint clean

up:
	docker compose up --build

down:
	docker compose down

build:
	docker compose build

test:
	pytest -q

lint:
	python -m compileall relay endpoint shared

clean:
	rm -rf relay/__pycache__ endpoint/__pycache__ shared/__pycache__ tests/__pycache__
