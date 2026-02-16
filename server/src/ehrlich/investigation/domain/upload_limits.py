"""Upload constraints — single source of truth for the entire application."""

from __future__ import annotations

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_FILES_PER_INVESTIGATION = 10
ALLOWED_EXTENSIONS = frozenset({"csv", "xlsx", "pdf"})
