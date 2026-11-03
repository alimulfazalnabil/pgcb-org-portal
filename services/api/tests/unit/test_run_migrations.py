from unittest.mock import patch
from scripts.run_migrations import mask_sensitive, run_migrations


def test_mask_sensitive_database_url_and_secrets():
    raw = "postgresql://myuser:P@ssword123@127.0.0.1:5432/mydb?sslmode=require token=abc12345"
    masked = mask_sensitive(raw)
    assert "P@ssword123" not in masked
    assert "abc12345" not in masked
    assert "postgresql://myuser:***@127.0.0.1:5432/mydb?sslmode=require" in masked


def test_run_migrations_uses_configured_database_url():
    with patch("alembic.command.upgrade") as mock_upgrade:
        exit_code = run_migrations()
        assert exit_code == 0
        mock_upgrade.assert_called_once()
        alembic_cfg = mock_upgrade.call_args[0][0]
        # Verify sqlalchemy.url was set
        assert alembic_cfg.get_main_option("sqlalchemy.url") is not None
