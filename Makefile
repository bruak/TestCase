COMPOSE_DIR := ./

all: up

up:
	@echo "initializing..."
	docker compose -f $(COMPOSE_DIR)/docker-compose.yml up -d --build

start:
	@echo "initializing..."
	docker compose -f $(COMPOSE_DIR)/docker-compose.yml start

down:
	@echo "Stopping..."
	docker compose -f $(COMPOSE_DIR)/docker-compose.yml down

stop:
	@echo "Stopping..."
	docker compose -f $(COMPOSE_DIR)/docker-compose.yml stop

restart: down up

build:
	@echo "Rebuilding..."
	docker compose -f $(COMPOSE_DIR)/docker-compose.yml build

clean:
	@echo "Removing temp files..."
	docker compose -f $(COMPOSE_DIR)/docker-compose.yml down --volumes --remove-orphans

fclean: clean
	@echo "Containers and images are completely cleaned..."
	docker compose -f $(COMPOSE_DIR)/docker-compose.yml down --rmi all --volumes --remove-orphans

re: fclean all

logs:
	docker compose -f $(COMPOSE_DIR)/docker-compose.yml logs -f

f:
	docker builder prune -a --force
	docker system prune -a --volumes --force
	docker volume prune --all --force

.PHONY: all up down restart build clean fclean re
