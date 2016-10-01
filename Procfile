web: gunicorn app:app
worker: celery -A tasks.py worker -B --loglevel=info

