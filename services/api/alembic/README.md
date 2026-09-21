# Alembic migrations

Run from `services/api`:

```bash
PYTHONPATH=. alembic upgrade head
PYTHONPATH=. alembic revision --autogenerate -m "describe change"
```

Production deployments should run migrations before the application is switched to the new release.
