from sqlalchemy import Column, DateTime, func, insert, String, Text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from workers.config import settings

Base = declarative_base()


class AuditLog(Base):
    __tablename__ = "audit_logs"

    audit_log_id = Column(String(36), primary_key=True)
    trace_id = Column(String(64), nullable=False)
    operator_id = Column(String(36), nullable=False)
    operator_role = Column(String(32), nullable=False)
    action = Column(String(64), nullable=False)
    resource_type = Column(String(64))
    resource_id = Column(String(36))
    details_jsonb = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


engine = None
AsyncSessionLocal = None


def init_engine() -> None:
    global engine, AsyncSessionLocal
    if engine is None:
        engine = create_async_engine(settings.database_url, echo=settings.debug)
        AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def write_audit_log(
    audit_log_id: str,
    trace_id: str,
    operator_id: str,
    operator_role: str,
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    details_jsonb: str | None = None,
) -> None:
    init_engine()
    async with AsyncSessionLocal() as session:
        stmt = insert(AuditLog).values(
            audit_log_id=audit_log_id,
            trace_id=trace_id,
            operator_id=operator_id,
            operator_role=operator_role,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details_jsonb=details_jsonb,
        )
        await session.execute(stmt)
        await session.commit()