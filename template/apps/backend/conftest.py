{% raw %}
import os

# Set DATABASE_URL before app modules are imported.
# Both conftest files are loaded before pytest_configure hooks fire,
# but root conftest loads before tests/conftest.py, so this runs in time.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
{% endraw %}
