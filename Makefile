.PHONY: help build up down restart logs clean

help:
	@echo "Compliance Analysis System - Docker Commands"
	@echo ""
	@echo "Usage: make [command]"
	@echo ""
	@echo "Commands:"
	@echo "  build       Build Docker images"
	@echo "  up          Start all services"
	@echo "  down        Stop all services"
	@echo "  restart     Restart all services"
	@echo "  logs        View logs (all services)"
	@echo "  logs-backend View backend logs"
	@echo "  logs-frontend View frontend logs"
	@echo "  clean       Stop and remove all containers, networks, and volumes"
	@echo "  shell-backend Open shell in backend container"
	@echo "  shell-frontend Open shell in frontend container"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Services started!"
	@echo "Frontend: http://localhost"
	@echo "Backend API: http://localhost:8000"

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

clean:
	docker-compose down -v
	@echo "All containers, networks, and volumes removed!"

shell-backend:
	docker-compose exec backend /bin/bash

shell-frontend:
	docker-compose exec frontend /bin/sh
