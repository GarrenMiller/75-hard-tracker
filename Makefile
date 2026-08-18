AUTHELIA_IMAGE ?= authelia/authelia:4.38
PROD_COMPOSE := docker compose -f docker-compose.yml -f docker-compose.prod.yml

.PHONY: up down build logs test api-shell web-shell prod-up prod-down prod-logs prod-ps authelia-hash

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

prod-up:
	$(PROD_COMPOSE) up -d --build

prod-down:
	$(PROD_COMPOSE) down

prod-logs:
	$(PROD_COMPOSE) logs -f

prod-ps:
	$(PROD_COMPOSE) ps

authelia-hash:
	docker run --rm $(AUTHELIA_IMAGE) authelia crypto hash generate argon2 --password '$(PASSWORD)'
