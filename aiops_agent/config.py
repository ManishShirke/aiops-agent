import os

# DB Settings
DB_NAME = "ops_sre.db"

# Model Settings
# We use flash-lite for speed/cost, falling back to flash standard if needed
MODEL_PRIMARY = "gemini-2.5-flash-lite"
MODEL_FALLBACK = "gemini-2.0-flash-lite"

# Agent Limits
MAX_LOOPS = 3        # Max retry attempts for fixing an issue
MEMORY_LIMIT = 3     # Number of incidents to keep before compacting history
