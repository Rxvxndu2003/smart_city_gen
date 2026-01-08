"""
Script to configure Alembic for database migrations
Run this after: alembic init alembic
"""
import os
from pathlib import Path

# Get the backend directory
BACKEND_DIR = Path(__file__).parent.parent
ALEMBIC_DIR = BACKEND_DIR / "alembic"
ENV_PY = ALEMBIC_DIR / "env.py"
ALEMBIC_INI = BACKEND_DIR / "alembic.ini"

# New env.py content
ENV_PY_CONTENT = '''from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import your models
from app.database import Base
from app.models.user import User, Role, UserRole
from app.models.project import Project
from app.models.site_volume import SiteVolume
from app.models.layout import Layout
from app.models.generation_job import GenerationJob
from app.models.validation_report import ValidationReport
from app.models.approval import Approval, ApprovalAssignment
from app.models.export import Export
from app.models.notification import Notification
from app.models.system_setting import SystemSetting
from app.models.blockchain_record import BlockchainRecord
from app.models.audit_log import AuditLog

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the SQLAlchemy URL from environment variable
from app.config import settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''

# Update alembic.ini to not require hardcoded database URL
ALEMBIC_INI_UPDATES = '''
# Update the sqlalchemy.url line to:
# sqlalchemy.url = 
# (Leave it empty, we'll set it from env.py using settings)
'''

def setup_alembic():
    """Configure Alembic files"""
    print("Setting up Alembic configuration...")
    
    if not ALEMBIC_DIR.exists():
        print("❌ Alembic directory not found!")
        print("Please run: alembic init alembic")
        return False
    
    # Write env.py
    print(f"✅ Writing {ENV_PY}")
    ENV_PY.write_text(ENV_PY_CONTENT)
    
    # Update alembic.ini
    print(f"✅ Updating {ALEMBIC_INI}")
    ini_content = ALEMBIC_INI.read_text()
    
    # Replace the sqlalchemy.url line
    lines = ini_content.split('\n')
    new_lines = []
    for line in lines:
        if line.startswith('sqlalchemy.url ='):
            new_lines.append('# sqlalchemy.url will be set from env.py using config.py settings')
            new_lines.append('sqlalchemy.url = ')
        else:
            new_lines.append(line)
    
    ALEMBIC_INI.write_text('\n'.join(new_lines))
    
    print("\n✅ Alembic configuration complete!")
    print("\nNext steps:")
    print("1. Ensure MySQL is running and database 'smart_city' exists")
    print("2. Run: alembic revision --autogenerate -m 'Initial migration'")
    print("3. Run: alembic upgrade head")
    print("4. Run: python scripts/create_admin.py")
    
    return True

if __name__ == "__main__":
    setup_alembic()
