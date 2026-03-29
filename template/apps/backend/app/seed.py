{% raw %}
"""
Seed the database with an admin user and sample items.
Run with: just seed
"""

import asyncio

from sqlalchemy import select

from app.auth import hash_password
from app.config import settings
from app.database import Base, async_session_maker, engine
from app.models.item import Item
from app.models.user import User


SAMPLE_ITEMS = [
    {
        "title": "Set up CI/CD pipeline",
        "description": "Configure GitHub Actions for the project",
    },
    {
        "title": "Write API documentation",
        "description": "Document all endpoints in OpenAPI spec",
    },
    {
        "title": "Add pagination",
        "description": "Implement cursor-based pagination for list endpoints",
    },
    {
        "title": "Set up monitoring",
        "description": "Add health checks and structured logging",
    },
    {
        "title": "Review security headers",
        "description": "Ensure proper CORS, CSP, and HSTS configuration",
    },
    {
        "title": "Write integration tests",
        "description": "Cover all CRUD operations with tests",
    },
    {
        "title": "Optimize database queries",
        "description": "Add indexes and review N+1 queries",
    },
    {
        "title": "Create user onboarding flow",
        "description": "Build registration and welcome screens",
    },
    {"title": "Implement search", "description": "Add full-text search for items"},
    {
        "title": "Deploy to staging",
        "description": "Set up staging environment with Docker",
    },
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        # Create admin user if not exists
        result = await session.execute(
            select(User).where(User.email == settings.admin_email)
        )
        admin = result.scalar_one_or_none()

        if not admin:
            admin = User(
                email=settings.admin_email,
                hashed_password=hash_password(settings.admin_password),
                full_name="Admin",
                is_active=True,
                is_superuser=True,
            )
            session.add(admin)
            await session.commit()
            await session.refresh(admin)
            print(f"Created admin user: {settings.admin_email}")
        else:
            print(f"Admin user already exists: {settings.admin_email}")

        # Create sample items if none exist
        result = await session.execute(select(Item).limit(1))
        if not result.scalar_one_or_none():
            for item_data in SAMPLE_ITEMS:
                item = Item(**item_data, owner_id=admin.id)
                session.add(item)
            await session.commit()
            print(f"Created {len(SAMPLE_ITEMS)} sample items")
        else:
            print("Items already exist, skipping seed")


if __name__ == "__main__":
    asyncio.run(seed())
{% endraw %}
