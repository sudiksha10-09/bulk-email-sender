.PHONY: help install migrate test run celery beat docker-up docker-down clean

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make migrate      - Run database migrations"
	@echo "  make test         - Run tests"
	@echo "  make run          - Run development server"
	@echo "  make celery       - Run Celery worker"
	@echo "  make beat         - Run Celery beat scheduler"
	@echo "  make docker-up    - Start Docker containers"
	@echo "  make docker-down  - Stop Docker containers"
	@echo "  make clean        - Clean Python cache files"

install:
	pip install --upgrade pip
	pip install -r requirements.txt

migrate:
	python manage.py migrate

test:
	pytest

test-coverage:
	pytest --cov=apps --cov-report=html --cov-report=term

run:
	python manage.py runserver

celery:
	celery -A config worker -l info

beat:
	celery -A config beat -l info

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".hypothesis" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -f .coverage

superuser:
	python manage.py createsuperuser

shell:
	python manage.py shell

makemigrations:
	python manage.py makemigrations

collectstatic:
	python manage.py collectstatic --noinput
