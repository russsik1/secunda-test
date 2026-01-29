from __future__ import annotations

from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Building(Base):
    __tablename__ = "buildings"
    __table_args__ = (
        Index("ix_buildings_address", "address"),
        Index("ix_buildings_lat_lon", "latitude", "longitude"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    address: Mapped[str] = mapped_column(nullable=False)
    latitude: Mapped[float] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)

    organizations: Mapped[list[Organization]] = relationship(back_populates="building")  # type: ignore[name-defined]


class Activity(Base):
    __tablename__ = "activities"
    __table_args__ = (
        CheckConstraint("level >= 1 AND level <= 3", name="ck_activities_level_1_3"),
        UniqueConstraint("parent_id", "name", name="uq_activities_parent_name"),
        Index("ix_activities_name", "name"),
        Index("ix_activities_parent_id", "parent_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("activities.id", ondelete="SET NULL"),
        nullable=True,
    )
    level: Mapped[int] = mapped_column(nullable=False)

    parent: Mapped[Optional[Activity]] = relationship(remote_side=[id], back_populates="children")
    children: Mapped[list[Activity]] = relationship(back_populates="parent")

    organizations: Mapped[list[Organization]] = relationship(  # type: ignore[name-defined]
        secondary=lambda: organization_activities,
        back_populates="activities",
    )


organization_activities = Table(
    "organization_activities",
    Base.metadata,
    Column("organization_id", Integer, ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True),
    Column("activity_id", Integer, ForeignKey("activities.id", ondelete="CASCADE"), primary_key=True),
    Index("ix_org_activities_activity_id", "activity_id"),
    Index("ix_org_activities_organization_id", "organization_id"),
)


class Organization(Base):
    __tablename__ = "organizations"
    __table_args__ = (
        Index("ix_organizations_name", "name"),
        Index("ix_organizations_building_id", "building_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    building_id: Mapped[int] = mapped_column(
        ForeignKey("buildings.id", ondelete="RESTRICT"),
        nullable=False,
    )

    building: Mapped[Building] = relationship(back_populates="organizations")
    phones: Mapped[list[OrganizationPhone]] = relationship(  # type: ignore[name-defined]
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    activities: Mapped[list[Activity]] = relationship(
        secondary=lambda: organization_activities,
        back_populates="organizations",
    )


class OrganizationPhone(Base):
    __tablename__ = "organization_phones"
    __table_args__ = (
        UniqueConstraint("organization_id", "phone", name="uq_org_phones_org_phone"),
        Index("ix_org_phones_organization_id", "organization_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    phone: Mapped[str] = mapped_column(String(64), nullable=False)

    organization: Mapped[Organization] = relationship(back_populates="phones")

