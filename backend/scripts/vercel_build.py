"""Vercel build step: apply database migrations before the new version goes live.

Runs after dependencies are installed. Needs DATABASE_URL in the project's environment variables
(build-time). Without it (for example a preview deployment with no database) the step is skipped.
"""
import os
import subprocess
import sys

if not os.environ.get("DATABASE_URL"):
    print("DATABASE_URL is not set: skipping migrations")
    sys.exit(0)
print("Applying database migrations...")
subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
print("Migrations applied")
