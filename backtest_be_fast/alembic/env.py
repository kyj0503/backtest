from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# P2-28: alembic.ini의 sqlalchemy.url은 플레이스홀더다. 여기서
# app.services.database.database_config.DatabaseConfig를 재사용해 런타임
# 애플리케이션(connection_manager.py)과 동일한 우선순위로 접속 URL을 만들고
# 덮어쓴다: DATABASE_URL 환경변수가 있으면 그대로, 없으면
# DATABASE_HOST/PORT/USER/PASSWORD/NAME 조합(각각 기본값 보유)으로 조립한다.
# alembic을 backtest_be_fast/ 에서 실행하면(alembic.ini의 prepend_sys_path=.)
# app 패키지를 import할 수 있다. 그 밖의 위치에서 실행되는 극단적인 경우에는
# DATABASE_URL만 직접 폴백으로 사용한다.
try:
    from app.services.database.database_config import DatabaseConfig

    config.set_main_option("sqlalchemy.url", DatabaseConfig().get_url())
except ImportError:
    import os

    if os.getenv("DATABASE_URL"):
        config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
#
# P2-28: 이 코드베이스는 SQLAlchemy ORM 모델(Declarative Base)이 없다 — DB
# 접근은 app/services/database/connection_manager.py의 Engine + raw SQL로
# 이뤄진다. 따라서 비교할 ORM 메타데이터가 없어 autogenerate는 쓸 수 없다.
# 새 리비전은 `alembic revision -m "..."`로 빈 파일을 만든 뒤 손으로
# 채운다 (versions/622933e2fe2e_initial_schema.py 참고).
target_metadata = None

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
