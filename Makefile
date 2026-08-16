.PHONY: up down build logs test api-shell web-shell

up:
	docker compose up --build

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

test:
	docker compose run --rm test pytest

api-shell:
	docker compose exec api sh

web-shell:
	docker compose exec web sh
