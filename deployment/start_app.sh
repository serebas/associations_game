#!/bin/bash
source /chat_env/bin/activate
cd /code

echo "----- Collect static files ------ "
python manage.py collectstatic --noinput

echo "-----------Apply migration--------- "
python manage.py makemigrations
python manage.py migrate


echo "-----------Run gunicorn--------- "
gunicorn -b :8000 chatProj.wsgi:application