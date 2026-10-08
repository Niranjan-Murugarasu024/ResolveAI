import asyncio
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import engine, Base, AsyncSessionLocal
from app.models.db_models import Customer, Subscription, ApiKey, Ticket, AuditLog

async def seed():
    print("Initializing database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Check if already seeded
        from sqlalchemy.future import select
        res = await session.execute(select(Customer))
        if res.scalars().first():
            print("Database already contains records. Skipping seed.")
            return

        print("Seeding customers...")
        c1 = Customer(id="CUS-1023", name="Acme Cloud Infrastructure", email="engineering@acmecloud.io", plan="pro", status="active")
        c2 = Customer(id="CUS-2045", name="FinTech Scale Corp", email="security@fintechscale.com", plan="enterprise", status="active")
        c3 = Customer(id="CUS-3011", name="DevStudio Labs", email="support@devstudio.dev", plan="free", status="active")
        session.add_all([c1, c2, c3])

        print("Seeding subscriptions...")
        s1 = Subscription(id="SUB-01", customer_id="CUS-1023", plan="pro", status="active", monthly_quota=50000, used_quota=14200)
        s2 = Subscription(id="SUB-02", customer_id="CUS-2045", plan="enterprise", status="active", monthly_quota=500000, used_quota=85300)
        s3 = Subscription(id="SUB-03", customer_id="CUS-3011", plan="free", status="active", monthly_quota=1000, used_quota=980)
        session.add_all([s1, s2, s3])

        print("Seeding API keys...")
        k1 = ApiKey(id="KEY-01", customer_id="CUS-1023", key_prefix="key_prod_9a4f", environment="production", status="active")
        k2 = ApiKey(id="KEY-02", customer_id="CUS-2045", key_prefix="key_prod_b7c2", environment="production", status="active")
        k3 = ApiKey(id="KEY-03", customer_id="CUS-3011", key_prefix="key_test_10d9", environment="test", status="active")
        session.add_all([k1, k2, k3])

        await session.commit()
        print("Database seed complete!")

if __name__ == "__main__":
    asyncio.run(seed())
