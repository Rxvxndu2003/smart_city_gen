"""
SQLAlchemy ORM models initialization.
Imports all models to make them available for Alembic migrations.
"""
from app.database import Base
from app.models.user import User
from app.models.role import Role, UserRole
from app.models.project import Project
from app.models.site_volume import SiteVolume
from app.models.layout import Layout, GenerationJob
from app.models.validation_report import ValidationReport
from app.models.approval import Approval, ApprovalAssignment
from app.models.export import Export
from app.models.notification import Notification
from app.models.system_setting import SystemSetting
from app.models.blockchain_record import BlockchainRecord
from app.models.audit_log import AuditLog
from app.models.analysis_result import AnalysisResult, AnalysisType

__all__ = [
    "Base",
    "User",
    "Role",
    "UserRole",
    "Project",
    "SiteVolume",
    "Layout",
    "GenerationJob",
    "ValidationReport",
    "Approval",
    "ApprovalAssignment",
    "Export",
    "Notification",
    "SystemSetting",
    "BlockchainRecord",
    "AuditLog",
    "AnalysisResult",
    "AnalysisType",
]
