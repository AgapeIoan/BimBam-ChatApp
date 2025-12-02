import os

# Provide defaults so pydantic settings can initialize during tests without external env.
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("DATABASE__DB_URL", "postgresql+asyncpg://user:pass@localhost:5432/db")
os.environ.setdefault("DATABASE__DB_HOST", "localhost")
os.environ.setdefault("DATABASE__DB_PORT", "5432")
os.environ.setdefault("DATABASE__DB_USER", "user")
os.environ.setdefault("DATABASE__DB_PASSWORD", "pass")
os.environ.setdefault("DATABASE__DB_NAME", "db")
