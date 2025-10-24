from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "postgresql+asyncpg://postgres:0200@localhost:5432/rental_bot"

engine = create_async_engine(DATABASE_URL, echo=False)
Base = declarative_base()
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    car = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    date_from = Column(String, nullable=False)
    date_to = Column(String, nullable=False)
    total = Column(Integer, nullable=False)
    status = Column(String, default="new")
    passport_photo = Column(String, nullable=True)



async def save_order(data: dict):
    async with async_session() as session:
        order = Order(
            name=data["name"],
            phone=data["phone"],
            car=data["car"],
            price=data["price"],
            date_from=data["date_from"],
            date_to=data["date_to"],
            total=data["total"],
            status="approved",
        )
        session.add(order)
        await session.commit()
        return order.id


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
