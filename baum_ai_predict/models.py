from datetime import datetime
from sqlalchemy import MetaData, Table, Column, Integer, String, TIMESTAMP, ForeignKey, JSON, Boolean, DATE, TEXT, \
    NUMERIC, UUID
import uuid

metadata = MetaData()

user = Table(
    "user",
    metadata,
    Column("id", UUID, default=uuid.uuid4, primary_key=True, index=True, nullable=False),
    Column("email", String, nullable=False),
    Column("name", String, nullable=False),
    Column("surname", String),
    Column("patronymic", String),
    Column("phone", String),
    Column("registered_at", TIMESTAMP, default=datetime.utcnow),
    Column("hashed_password", String, nullable=False),
    Column("is_active", Boolean, default=True, nullable=False),
    Column("is_superuser", Boolean, default=False, nullable=False),
    Column("is_verified", Boolean, default=False, nullable=False),
)

real_data = Table(
    "real_data",
    metadata,
    Column("sn", TEXT),
    Column("object type", TEXT),
    Column("object", TEXT),
    Column("time", DATE),
    Column("Capacity usage(%)", NUMERIC),
    Column("Mapped LUN capacity(MB)", NUMERIC),
    Column("Total capacity(MB)", NUMERIC),
    Column("Used capacity(MB)", NUMERIC),
    Column("array_num", TEXT),
)

