# Convenience commands — run from project root

# Start full dev stack (Django + Celery + Channels)
dev:
	python manage.py runserver

worker:
	celery -A config.celery worker --loglevel=info

beat:
	celery -A config.celery beat --loglevel=info

flower:
	celery -A config.celery flower --port=5555

# Database
migrate:
	python manage.py makemigrations && python manage.py migrate

shell:
	python manage.py shell_plus

# Tests
test:
	pytest apps/ --tb=short -q

test-cov:
	pytest apps/ --cov=apps --cov-report=html

# Docker
up:
	docker-compose up -d

down:
	docker-compose down

# Code quality
lint:
	ruff check . && black --check .

fmt:
	black . && ruff --fix .
