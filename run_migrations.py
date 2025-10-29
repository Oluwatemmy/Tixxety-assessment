# run_migrations.py
import os
from alembic import command
from dotenv import load_dotenv
from alembic.config import Config

# Load environment variables
load_dotenv()

# Point to your Alembic directory
alembic_cfg = Config("alembic.ini")

print("🚀 Upgrading to head...")
command.upgrade(alembic_cfg, "head")

print("✅ Migration complete.")
