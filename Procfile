release: python migrations/pre_deploy.py
web: gunicorn --worker-class eventlet -w 1 manage:app