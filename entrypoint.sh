#!/bin/sh

if [ "$WW4API_SKIP_ENTRYPOINT" = "1" ]; then
    echo "Skipping entrypoint script"
else
    if [ "$WW4API_POSTGRES_DB" = "postgres" ]; then
        echo "Waiting for postgres..."

        while ! nc -z "$WW4API_POSTGRES_HOST" "$WW4API_POSTGRES_PORT"; do
          sleep 0.1
        done

        echo "PostgreSQL started"
    fi

    python manage.py migrate
fi

exec "$@"
