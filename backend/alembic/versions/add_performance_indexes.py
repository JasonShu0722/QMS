"""add performance indexes

Revision ID: performance_indexes_001
Revises: 
Create Date: 2026-02-12 10:00:00.000000

添加性能优化索引
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'performance_indexes_001'
down_revision = None  # 替换为实际的前一个版本号
branch_labels = None
depends_on = None


def upgrade():
    """
    添加性能优化索引
    
    索引策略：
    1. 高频查询字段（如 user_id, supplier_id, status）
    2. 外键字段
    3. 时间范围查询字段（created_at, deadline）
    4. 组合索引（多字段联合查询）
    """
    
    # ============================================
    # Users Table Indexes (用户表索引)
    # ============================================
    op.create_index(
        'idx_users_username',
        'users',
        ['username'],
        unique=False
    )
    op.create_index(
        'idx_users_email',
        'users',
        ['email'],
        unique=False
    )
    op.create_index(
        'idx_users_status',
        'users',
        ['status'],
        unique=False
    )
    op.create_index(
        'idx_users_user_type',
        'users',
        ['user_type'],
        unique=False
    )
    op.create_index(
        'idx_users_supplier_id',
        'users',
        ['supplier_id'],
        unique=False
    )
    # 组合索引：按类型和状态查询用户
    op.create_index(
        'idx_users_type_status',
        'users',
        ['user_type', 'status'],
        unique=False
    )
    
    # ============================================
    # Permissions Table Indexes (权限表索引)
    # ============================================
    op.create_index(
        'idx_permissions_user_id',
        'permissions',
        ['user_id'],
        unique=False
    )
    op.create_index(
        'idx_permissions_module_path',
        'permissions',
        ['module_path'],
        unique=False
    )
    # 组合索引：权限检查（用户+模块+操作）
    op.create_index(
        'idx_permissions_user_module_op',
        'permissions',
        ['user_id', 'module_path', 'operation_type'],
        unique=False
    )
    
    # ============================================
    # Notifications Table Indexes (通知表索引)
    # ============================================
    op.create_index(
        'idx_notifications_user_id',
        'notifications',
        ['user_id'],
        unique=False
    )
    op.create_index(
        'idx_notifications_is_read',
        'notifications',
        ['is_read'],
        unique=False
    )
    op.create_index(
        'idx_notifications_created_at',
        'notifications',
        ['created_at'],
        unique=False
    )
    # 组合索引：查询用户未读消息
    op.create_index(
        'idx_notifications_user_unread',
        'notifications',
        ['user_id', 'is_read', 'created_at'],
        unique=False
    )
    
    # ============================================
    # Operation Logs Table Indexes (操作日志表索引)
    # ============================================
    op.create_index(
        'idx_operation_logs_user_id',
        'operation_logs',
        ['user_id'],
        unique=False
    )
    op.create_index(
        'idx_operation_logs_operation_type',
        'operation_logs',
        ['operation_type'],
        unique=False
    )
    op.create_index(
        'idx_operation_logs_target_type',
        'operation_logs',
        ['target_type'],
        unique=False
    )
    op.create_index(
        'idx_operation_logs_created_at',
        'operation_logs',
        ['created_at'],
        unique=False
    )
    # 组合索引：按用户和时间查询日志
    op.create_index(
        'idx_operation_logs_user_time',
        'operation_logs',
        ['user_id', 'created_at'],
        unique=False
    )
    
    # ============================================
    # Suppliers Table Indexes (供应商表索引)
    # ============================================
    op.create_index(
        'idx_suppliers_code',
        'suppliers',
        ['code'],
        unique=True
    )
    op.create_index(
        'idx_suppliers_name',
        'suppliers',
        ['name'],
        unique=False
    )
    op.create_index(
        'idx_suppliers_status',
        'suppliers',
        ['status'],
        unique=False
    )
    # 全文搜索索引（PostgreSQL GIN）
    op.execute("""
        CREATE INDEX idx_suppliers_name_gin 
        ON suppliers 
        USING gin(to_tsvector('simple', name))
    """)
    
    # ============================================
    # Feature Flags Table Indexes (功能开关表索引)
    # ============================================
    op.create_index(
        'idx_feature_flags_key',
        'feature_flags',
        ['feature_key'],
        unique=True
    )
    op.create_index(
        'idx_feature_flags_enabled',
        'feature_flags',
        ['is_enabled'],
        unique=False
    )
    op.create_index(
        'idx_feature_flags_environment',
        'feature_flags',
        ['environment'],
        unique=False
    )
    
    # ============================================
    # System Config Table Indexes (系统配置表索引)
    # ============================================
    op.create_index(
        'idx_system_config_key',
        'system_config',
        ['config_key'],
        unique=True
    )
    op.create_index(
        'idx_system_config_category',
        'system_config',
        ['category'],
        unique=False
    )
    
    # ============================================
    # Announcements Table Indexes (公告表索引)
    # ============================================
    op.create_index(
        'idx_announcements_is_active',
        'announcements',
        ['is_active'],
        unique=False
    )
    op.create_index(
        'idx_announcements_published_at',
        'announcements',
        ['published_at'],
        unique=False
    )
    op.create_index(
        'idx_announcements_importance',
        'announcements',
        ['importance'],
        unique=False
    )
    # 组合索引：查询有效的重要公告
    op.create_index(
        'idx_announcements_active_important',
        'announcements',
        ['is_active', 'importance', 'published_at'],
        unique=False
    )
    
    # ============================================
    # 业务表索引示例（根据实际业务表调整）
    # ============================================
    
    # SCAR Reports (供应商纠正措施请求)
    # op.create_index(
    #     'idx_scar_supplier_id',
    #     'scar_reports',
    #     ['supplier_id'],
    #     unique=False
    # )
    # op.create_index(
    #     'idx_scar_status',
    #     'scar_reports',
    #     ['status'],
    #     unique=False
    # )
    # op.create_index(
    #     'idx_scar_current_handler',
    #     'scar_reports',
    #     ['current_handler_id'],
    #     unique=False
    # )
    # op.create_index(
    #     'idx_scar_deadline',
    #     'scar_reports',
    #     ['deadline'],
    #     unique=False
    # )
    
    print("✅ 性能优化索引创建完成")


def downgrade():
    """
    删除性能优化索引
    """
    
    # Users
    op.drop_index('idx_users_type_status', table_name='users')
    op.drop_index('idx_users_supplier_id', table_name='users')
    op.drop_index('idx_users_user_type', table_name='users')
    op.drop_index('idx_users_status', table_name='users')
    op.drop_index('idx_users_email', table_name='users')
    op.drop_index('idx_users_username', table_name='users')
    
    # Permissions
    op.drop_index('idx_permissions_user_module_op', table_name='permissions')
    op.drop_index('idx_permissions_module_path', table_name='permissions')
    op.drop_index('idx_permissions_user_id', table_name='permissions')
    
    # Notifications
    op.drop_index('idx_notifications_user_unread', table_name='notifications')
    op.drop_index('idx_notifications_created_at', table_name='notifications')
    op.drop_index('idx_notifications_is_read', table_name='notifications')
    op.drop_index('idx_notifications_user_id', table_name='notifications')
    
    # Operation Logs
    op.drop_index('idx_operation_logs_user_time', table_name='operation_logs')
    op.drop_index('idx_operation_logs_created_at', table_name='operation_logs')
    op.drop_index('idx_operation_logs_target_type', table_name='operation_logs')
    op.drop_index('idx_operation_logs_operation_type', table_name='operation_logs')
    op.drop_index('idx_operation_logs_user_id', table_name='operation_logs')
    
    # Suppliers
    op.execute("DROP INDEX IF EXISTS idx_suppliers_name_gin")
    op.drop_index('idx_suppliers_status', table_name='suppliers')
    op.drop_index('idx_suppliers_name', table_name='suppliers')
    op.drop_index('idx_suppliers_code', table_name='suppliers')
    
    # Feature Flags
    op.drop_index('idx_feature_flags_environment', table_name='feature_flags')
    op.drop_index('idx_feature_flags_enabled', table_name='feature_flags')
    op.drop_index('idx_feature_flags_key', table_name='feature_flags')
    
    # System Config
    op.drop_index('idx_system_config_category', table_name='system_config')
    op.drop_index('idx_system_config_key', table_name='system_config')
    
    # Announcements
    op.drop_index('idx_announcements_active_important', table_name='announcements')
    op.drop_index('idx_announcements_importance', table_name='announcements')
    op.drop_index('idx_announcements_published_at', table_name='announcements')
    op.drop_index('idx_announcements_is_active', table_name='announcements')
    
    print("✅ 性能优化索引删除完成")
