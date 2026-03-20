release: python backend/manage.py migrate --noinput
web: python backend/manage.py collectstatic --noinput && gunicorn --bind 0.0.0.0:8080 --pythonpath backend gradus.wsgi