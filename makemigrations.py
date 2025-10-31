from alembic import command
from datetime import datetime
from dotenv import load_dotenv
from alembic.config import Config

# Step 1: Load environment variables (DATABASE_URL, etc.)
load_dotenv()

# Step 2: Configure Alembic
alembic_cfg = Config("alembic.ini")

# Optional: Provide a name based on timestamp
revision_msg = f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Step 3: Autogenerate a new revision
print(f"🔧 Creating migration: {revision_msg}")
command.revision(alembic_cfg, message=revision_msg, autogenerate=True)

print(f"✅ Migration {revision_msg} created successfully.")
