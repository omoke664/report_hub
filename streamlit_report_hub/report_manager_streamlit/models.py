# models.py
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Table, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime
import uuid

Base = declarative_base()

def gen_uuid():
    """Generate a string UUID."""
    return str(uuid.uuid4())

# -----------------------------
# Association table for User <-> Group
# -----------------------------
group_members = Table(
    "group_members",
    Base.metadata,
    Column("user_id", String, ForeignKey("users.id"), primary_key=True),
    Column("group_id", String, ForeignKey("groups.id"), primary_key=True)
)

# -----------------------------
# Role model
# -----------------------------
class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

# -----------------------------
# User model
# -----------------------------
class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=gen_uuid)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=True)
    invite_token = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))

    role = relationship("Role")
    organization = relationship("Organization", back_populates="users")
    reports = relationship("Report", back_populates="owner", cascade="all, delete-orphan")
    groups = relationship("Group", secondary=group_members, back_populates="users")

# -----------------------------
# Organization model
# -----------------------------
class Organization(Base):
    __tablename__ = "organizations"
    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))

    users = relationship("User", back_populates="organization")
    groups = relationship("Group", back_populates="organization")
    reports = relationship("Report", back_populates="organization", cascade="all, delete-orphan")
    folders = relationship("Folder", back_populates="organization")
    dashboards = relationship("Dashboard", back_populates="organization", cascade="all, delete-orphan")

# -----------------------------
# Group model
# -----------------------------
class Group(Base):
    __tablename__ = "groups"
    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))

    organization = relationship("Organization", back_populates="groups")
    users = relationship("User", secondary=group_members, back_populates="groups")

# -----------------------------
# Folder model
# -----------------------------
class Folder(Base):
    __tablename__ = "folders"
    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))

    organization = relationship("Organization", back_populates="folders")
    reports = relationship("Report", back_populates="folder")

# -----------------------------
# Report model
# -----------------------------
class Report(Base):
    __tablename__ = "reports"
    id = Column(String, primary_key=True, default=gen_uuid)
    title = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    folder_id = Column(String, ForeignKey("folders.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    owner = relationship("User", back_populates="reports")
    organization = relationship("Organization", back_populates="reports")
    folder = relationship("Folder", back_populates="reports")
    permissions = relationship("ReportPermission", back_populates="report", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="report", cascade="all, delete-orphan")

class ReportPermission(Base):
    __tablename__ = "report_permissions"
    id = Column(String, primary_key=True, default=gen_uuid)
    report_id = Column(String, ForeignKey("reports.id"))
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    group_id = Column(String, ForeignKey("groups.id"), nullable=True)
    level = Column(String, nullable=False)  # Viewer, Commenter, Editor, Owner

    report = relationship("Report", back_populates="permissions")
    user = relationship("User")
    group = relationship("Group")

# -----------------------------
# Dashboard model
# -----------------------------
class Dashboard(Base):
    __tablename__ = "dashboards"
    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    description = Column(String, default="No description provided")
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    created_by_id = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))

    organization = relationship("Organization", back_populates="dashboards")
    created_by = relationship("User")
    visualizations = relationship(
        "Visualization",
        back_populates="dashboard",
        cascade="all, delete-orphan",
        order_by="Visualization.position"
    )
    permissions = relationship(
        "DashboardPermission",
        back_populates="dashboard",
        cascade="all, delete-orphan"
    )

class Visualization(Base):
    __tablename__ = "visualizations"
    id = Column(String, primary_key=True, default=gen_uuid)
    dashboard_id = Column(String, ForeignKey("dashboards.id"), nullable=False)
    title = Column(String, nullable=False)
    type = Column(String, nullable=False)  # Bar, Line, Pie, Table
    data_config = Column(JSON, nullable=False)
    position = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))

    dashboard = relationship("Dashboard", back_populates="visualizations")

class DashboardPermission(Base):
    __tablename__ = "dashboard_permissions"
    id = Column(String, primary_key=True, default=gen_uuid)
    dashboard_id = Column(String, ForeignKey("dashboards.id"))
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    group_id = Column(String, ForeignKey("groups.id"), nullable=True)
    level = Column(String, nullable=False)  # Viewer, Editor

    dashboard = relationship("Dashboard", back_populates="permissions")
    user = relationship("User")
    group = relationship("Group")

class Comment(Base):
    __tablename__ = "comments"
    id = Column(String, primary_key=True, default=gen_uuid)
    report_id = Column(String, ForeignKey("reports.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    comment = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))

    report = relationship("Report", back_populates="comments")
    user = relationship("User")
