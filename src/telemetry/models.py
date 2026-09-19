from datetime import datetime

from sqlalchemy import BigInteger, Float, Index, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from telemetry.db import Base


class Telemetry(Base):
    __tablename__ = "telemetry"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[int] = mapped_column(BigInteger, nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False)
    voltage_mv: Mapped[int] = mapped_column(Integer, nullable=False)
    frame_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    received_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    __table_args__ = (Index("ix_telemetry_timestamp", "timestamp"),)
    