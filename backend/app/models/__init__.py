# Database Models
from app.models.base import Base
from app.models.supplier import Supplier, SupplierStatus
from app.models.user import User, UserType, UserStatus
from app.models.permission import Permission, OperationType
from app.models.feature_flag import FeatureFlag, FeatureFlagScope, FeatureFlagEnvironment
from app.models.system_config import SystemConfig, ConfigCategory
from app.models.notification import Notification, MessageType
from app.models.announcement import Announcement, AnnouncementType, ImportanceLevel
from app.models.announcement_read_log import AnnouncementReadLog
from app.models.operation_log import OperationLog
from app.models.notification_rule import NotificationRule, ActionType
from app.models.smtp_config import SMTPConfig, TestResult
from app.models.instrument_calibration import InstrumentCalibration, CalibrationStatus
from app.models.quality_cost import QualityCost, CostType
from app.models.quality_metric import QualityMetric, MetricType
from app.models.ims_sync_log import IMSSyncLog, SyncStatus, SyncType

# Supplier Quality Management Models (供应商质量管理模型)
from app.models.scar import SCAR, SCARSeverity, SCARStatus
from app.models.eight_d import EightD, EightDStatus
from app.models.supplier_audit import SupplierAudit, AuditType, AuditResult
from app.models.supplier_performance import SupplierPerformance, PerformanceGrade
from app.models.supplier_target import SupplierTarget, TargetType
from app.models.ppap import PPAP, PPAPLevel, PPAPStatus
from app.models.inspection_spec import InspectionSpec, InspectionSpecStatus
from app.models.barcode_validation import BarcodeValidation, BarcodeScanRecord

__all__ = [
    "Base",
    "Supplier",
    "SupplierStatus",
    "User",
    "UserType",
    "UserStatus",
    "Permission",
    "OperationType",
    "FeatureFlag",
    "FeatureFlagScope",
    "FeatureFlagEnvironment",
    "SystemConfig",
    "ConfigCategory",
    "Notification",
    "MessageType",
    "Announcement",
    "AnnouncementType",
    "ImportanceLevel",
    "AnnouncementReadLog",
    "OperationLog",
    "NotificationRule",
    "ActionType",
    "SMTPConfig",
    "TestResult",
    "InstrumentCalibration",
    "CalibrationStatus",
    "QualityCost",
    "CostType",
    "QualityMetric",
    "MetricType",
    "IMSSyncLog",
    "SyncStatus",
    "SyncType",
    # Supplier Quality Management
    "SCAR",
    "SCARSeverity",
    "SCARStatus",
    "EightD",
    "EightDStatus",
    "SupplierAudit",
    "AuditType",
    "AuditResult",
    "SupplierPerformance",
    "PerformanceGrade",
    "SupplierTarget",
    "TargetType",
    "PPAP",
    "PPAPLevel",
    "PPAPStatus",
    "InspectionSpec",
    "InspectionSpecStatus",
    "BarcodeValidation",
    "BarcodeScanRecord",
]
