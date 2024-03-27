#!/bin/sh
if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

python manage.py migrate photologue
python manage.py migrate sites
python manage.py makemigrations services store customuser
python manage.py migrate
python manage.py collectstatic --no-input

echo "import os
from django.contrib.auth import get_user_model
# os.environ.get('SUPERUSER_NAME', default='admin')
try:
	User = get_user_model()
	User.objects.create_superuser(os.environ.get('SUPERUSER_EMAIL', default='admin@example.com'), os.environ.get('SUPERUSER_PASSWORD', default='1'))
except Exception:
    print('Superuser already exist!')
exit()
" | python manage.py shell

exec "$@"
