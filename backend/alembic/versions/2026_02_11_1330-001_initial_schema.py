"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2026-02-11 13:30:00.000000

本迁移脚本创建 QMS 系统的初始数据库架构，包括：
- 用户与权限管理表
- 通知与公告系统表
- 功能开关与系统配置表
- 预留功能表（仪器校准、质量成本）

所有新增字段均设置为 Nullable 或带有 Default Value，
遵循双轨发布的非破坏性迁移原则。
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    升级数据库架构
    创建所有核心表和预留功能表
    """
    
    # 1. 创建供应商表
    op.create_table(
        'suppliers',
        sa.Column('id', sa.Integer(), nullable=False, comment='供应商ID'),
        sa.Column('name', sa.String(length=200), nullable=False, comment='供应商名称'),
        sa.Column('code', sa.String(length=50), nullable=False, comment='供应商代码'),
        sa.Column('contact_person', sa.String(length=100), nullable=True, comment='联系人'),
        sa.Column('contact_email', sa.String(length=100), nullable=True, comment='联系邮箱'),
        sa.Column('contact_phone', sa.String(length=20), nullable=True, comment='联系电话'),
        sa.Column('iso9001_cert', sa.String(length=500), nullable=True, comment='ISO9001证书路径'),
        sa.Column('iso9001_expiry', sa.Date(), nullable=True, comment='ISO9001过期日期'),
        sa.Column('iatf16949_cert', sa.String(length=500), nullable=True, comment='IATF16949证书路径'),
        sa.Column('iatf16949_expiry', sa.Date(), nullable=True, comment='IATF16949过期日期'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending', comment='状态'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uq_supplier_code'),
        sa.CheckConstraint("status IN ('pending', 'active', 'suspended')", name='check_supplier_status')
    )
    op.create_index('ix_suppliers_id', 'suppliers', ['id'])
    op.create_index('ix_suppliers_code', 'suppliers', ['code'])
    op.create_index('ix_suppliers_status', 'suppliers', ['status'])
    
    # 2. 创建用户表
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('username', sa.String(length=50), nullable=False, comment='用户名'),
        sa.Column('hashed_password', sa.String(length=255), nullable=False, comment='密码哈希'),
        sa.Column('full_name', sa.String(length=100), nullable=False, comment='姓名'),
        sa.Column('email', sa.String(length=100), nullable=False, comment='邮箱'),
        sa.Column('phone', sa.String(length=20), nullable=True, comment='电话'),
        sa.Column('user_type', sa.String(length=20), nullable=False, comment='用户类型'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending', comment='状态'),
        sa.Column('department', sa.String(length=100), nullable=True, comment='部门'),
        sa.Column('position', sa.String(length=100), nullable=True, comment='职位'),
        sa.Column('supplier_id', sa.Integer(), nullable=True, comment='供应商ID'),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0', comment='失败登录次数'),
        sa.Column('locked_until', sa.DateTime(), nullable=True, comment='锁定截止时间'),
        sa.Column('password_changed_at', sa.DateTime(), nullable=True, comment='密码修改时间'),
        sa.Column('last_login_at', sa.DateTime(), nullable=True, comment='最后登录时间'),
        sa.Column('digital_signature', sa.String(length=500), nullable=True, comment='电子签名路径'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.Column('updated_by', sa.Integer(), nullable=True, comment='更新人ID'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username', name='uq_user_username'),
        sa.CheckConstraint("user_type IN ('internal', 'supplier')", name='check_user_type'),
        sa.CheckConstraint("status IN ('pending', 'active', 'frozen', 'rejected')", name='check_user_status')
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_status', 'users', ['status'])
    op.create_index('ix_users_supplier_id', 'users', ['supplier_id'])
    
    # 3. 创建权限表
    op.create_table(
        'permissions',
        sa.Column('id', sa.Integer(), nullable=False, comment='权限ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('module_path', sa.String(length=255), nullable=False, comment='模块路径'),
        sa.Column('operation_type', sa.String(length=20), nullable=False, comment='操作类型'),
        sa.Column('is_granted', sa.Boolean(), nullable=False, server_default='true', comment='是否授予'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'module_path', 'operation_type', name='uq_permission_user_module_op'),
        sa.CheckConstraint("operation_type IN ('create', 'read', 'update', 'delete', 'export')", name='check_operation_type')
    )
    op.create_index('ix_permissions_id', 'permissions', ['id'])
    op.create_index('ix_permissions_user_id', 'permissions', ['user_id'])
    op.create_index('ix_permissions_module_path', 'permissions', ['module_path'])
    
    # 4. 创建通知表
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False, comment='通知ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='接收用户ID'),
        sa.Column('message_type', sa.String(length=50), nullable=False, comment='消息类型'),
        sa.Column('title', sa.String(length=200), nullable=False, comment='消息标题'),
        sa.Column('content', sa.Text(), nullable=False, comment='消息内容'),
        sa.Column('link', sa.String(length=500), nullable=True, comment='跳转链接'),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false', comment='是否已读'),
        sa.Column('read_at', sa.DateTime(), nullable=True, comment='阅读时间'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("message_type IN ('workflow_exception', 'system_alert', 'warning')", name='check_message_type')
    )
    op.create_index('ix_notifications_id', 'notifications', ['id'])
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_is_read', 'notifications', ['is_read'])
    op.create_index('ix_notifications_created_at', 'notifications', ['created_at'])
    
    # 5. 创建公告表
    op.create_table(
        'announcements',
        sa.Column('id', sa.Integer(), nullable=False, comment='公告ID'),
        sa.Column('title', sa.String(length=200), nullable=False, comment='公告标题'),
        sa.Column('content', sa.Text(), nullable=False, comment='公告内容'),
        sa.Column('announcement_type', sa.String(length=50), nullable=False, comment='公告类型'),
        sa.Column('importance', sa.String(length=20), nullable=False, server_default='normal', comment='重要程度'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='是否激活'),
        sa.Column('published_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='发布时间'),
        sa.Column('expires_at', sa.DateTime(), nullable=True, comment='过期时间'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("announcement_type IN ('system', 'quality_warning', 'document_update')", name='check_announcement_type'),
        sa.CheckConstraint("importance IN ('normal', 'important')", name='check_importance')
    )
    op.create_index('ix_announcements_id', 'announcements', ['id'])
    op.create_index('ix_announcements_published_at', 'announcements', ['published_at'])
    op.create_index('ix_announcements_importance', 'announcements', ['importance'])
    
    # 6. 创建公告阅读记录表
    op.create_table(
        'announcement_read_logs',
        sa.Column('id', sa.Integer(), nullable=False, comment='记录ID'),
        sa.Column('announcement_id', sa.Integer(), nullable=False, comment='公告ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='阅读用户ID'),
        sa.Column('read_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='阅读时间'),
        sa.ForeignKeyConstraint(['announcement_id'], ['announcements.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('announcement_id', 'user_id', name='uq_announcement_user')
    )
    op.create_index('ix_announcement_read_logs_id', 'announcement_read_logs', ['id'])
    op.create_index('ix_announcement_read_logs_announcement_id', 'announcement_read_logs', ['announcement_id'])
    op.create_index('ix_announcement_read_logs_user_id', 'announcement_read_logs', ['user_id'])
    
    # 7. 创建操作日志表
    op.create_table(
        'operation_logs',
        sa.Column('id', sa.Integer(), nullable=False, comment='日志ID'),
        sa.Column('user_id', sa.Integer(), nullable=True, comment='操作用户ID'),
        sa.Column('operation_type', sa.String(length=50), nullable=False, comment='操作类型'),
        sa.Column('target_module', sa.String(length=100), nullable=False, comment='目标模块'),
        sa.Column('target_id', sa.Integer(), nullable=True, comment='目标对象ID'),
        sa.Column('before_data', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='操作前数据快照'),
        sa.Column('after_data', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='操作后数据快照'),
        sa.Column('ip_address', sa.String(length=45), nullable=True, comment='客户端IP地址'),
        sa.Column('user_agent', sa.Text(), nullable=True, comment='浏览器User-Agent'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='操作时间'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_operation_logs_id', 'operation_logs', ['id'])
    op.create_index('ix_operation_logs_user_id', 'operation_logs', ['user_id'])
    op.create_index('ix_operation_logs_operation_type', 'operation_logs', ['operation_type'])
    op.create_index('ix_operation_logs_target_module', 'operation_logs', ['target_module'])
    op.create_index('ix_operation_logs_created_at', 'operation_logs', ['created_at'])
    
    # 8. 创建功能特性开关表
    op.create_table(
        'feature_flags',
        sa.Column('id', sa.Integer(), nullable=False, comment='功能开关ID'),
        sa.Column('feature_key', sa.String(length=100), nullable=False, comment='功能键'),
        sa.Column('feature_name', sa.String(length=255), nullable=False, comment='功能名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='描述'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='false', comment='是否启用'),
        sa.Column('scope', sa.String(length=20), nullable=False, server_default='global', comment='作用域'),
        sa.Column('whitelist_user_ids', postgresql.ARRAY(sa.Integer()), nullable=True, comment='白名单用户ID列表'),
        sa.Column('whitelist_supplier_ids', postgresql.ARRAY(sa.Integer()), nullable=True, comment='白名单供应商ID列表'),
        sa.Column('environment', sa.String(length=20), nullable=True, comment='环境标识'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('updated_by', sa.Integer(), nullable=True, comment='更新人ID'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('feature_key', name='uq_feature_key'),
        sa.CheckConstraint("scope IN ('global', 'whitelist')", name='check_scope')
    )
    op.create_index('ix_feature_flags_id', 'feature_flags', ['id'])
    op.create_index('ix_feature_flags_feature_key', 'feature_flags', ['feature_key'])
    op.create_index('ix_feature_flags_is_enabled', 'feature_flags', ['is_enabled'])
    
    # 9. 创建系统配置表
    op.create_table(
        'system_configs',
        sa.Column('id', sa.Integer(), nullable=False, comment='配置ID'),
        sa.Column('config_key', sa.String(length=100), nullable=False, comment='配置键'),
        sa.Column('config_value', sa.Text(), nullable=False, comment='配置值'),
        sa.Column('value_type', sa.String(length=20), nullable=False, comment='值类型'),
        sa.Column('category', sa.String(length=50), nullable=True, comment='配置分类'),
        sa.Column('description', sa.Text(), nullable=True, comment='描述'),
        sa.Column('is_editable', sa.Boolean(), nullable=False, server_default='true', comment='是否可编辑'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('updated_by', sa.Integer(), nullable=True, comment='更新人ID'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('config_key', name='uq_config_key'),
        sa.CheckConstraint("value_type IN ('string', 'integer', 'boolean', 'json')", name='check_value_type')
    )
    op.create_index('ix_system_configs_id', 'system_configs', ['id'])
    op.create_index('ix_system_configs_config_key', 'system_configs', ['config_key'])
    
    # 插入默认系统配置
    op.execute("""
        INSERT INTO system_configs (config_key, config_value, value_type, category, description, is_editable) VALUES
        ('password_min_length', '8', 'integer', 'security', '密码最小长度', true),
        ('password_expire_days', '90', 'integer', 'security', '密码过期天数', true),
        ('login_max_attempts', '5', 'integer', 'security', '最大登录尝试次数', true),
        ('login_lock_minutes', '30', 'integer', 'security', '账号锁定时长（分钟）', true),
        ('jwt_expire_hours', '24', 'integer', 'security', 'JWT Token 有效期（小时）', true),
        ('todo_urgent_threshold_hours', '72', 'integer', 'business', '待办任务紧急阈值（小时）', true)
    """)
    
    # 10. 创建通知规则表
    op.create_table(
        'notification_rules',
        sa.Column('id', sa.Integer(), nullable=False, comment='规则ID'),
        sa.Column('rule_name', sa.String(length=200), nullable=False, comment='规则名称'),
        sa.Column('business_object', sa.String(length=100), nullable=False, comment='业务对象'),
        sa.Column('trigger_condition', postgresql.JSON(astext_type=sa.Text()), nullable=False, comment='触发条件JSON'),
        sa.Column('action_type', sa.String(length=50), nullable=False, comment='动作类型'),
        sa.Column('action_config', postgresql.JSON(astext_type=sa.Text()), nullable=False, comment='动作配置JSON'),
        sa.Column('escalation_enabled', sa.Boolean(), nullable=False, server_default='false', comment='是否启用超时升级'),
        sa.Column('escalation_hours', sa.Integer(), nullable=True, comment='超时小时数'),
        sa.Column('escalation_recipients', postgresql.ARRAY(sa.Integer()), nullable=True, comment='升级抄送人ID列表'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='是否激活'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("action_type IN ('send_email', 'send_notification', 'send_webhook')", name='check_action_type')
    )
    op.create_index('ix_notification_rules_id', 'notification_rules', ['id'])
    op.create_index('ix_notification_rules_business_object', 'notification_rules', ['business_object'])
    op.create_index('ix_notification_rules_is_active', 'notification_rules', ['is_active'])
    
    # 11. 创建SMTP配置表
    op.create_table(
        'smtp_configs',
        sa.Column('id', sa.Integer(), nullable=False, comment='配置ID'),
        sa.Column('config_name', sa.String(length=100), nullable=False, comment='配置名称'),
        sa.Column('smtp_host', sa.String(length=255), nullable=False, comment='SMTP服务器地址'),
        sa.Column('smtp_port', sa.Integer(), nullable=False, comment='SMTP端口'),
        sa.Column('smtp_user', sa.String(length=255), nullable=False, comment='SMTP用户名'),
        sa.Column('smtp_password_encrypted', sa.Text(), nullable=False, comment='SMTP密码（加密）'),
        sa.Column('use_tls', sa.Boolean(), nullable=False, server_default='true', comment='是否使用TLS'),
        sa.Column('from_email', sa.String(length=255), nullable=False, comment='发件人邮箱'),
        sa.Column('from_name', sa.String(length=100), nullable=True, comment='发件人名称'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='是否激活'),
        sa.Column('last_test_at', sa.DateTime(), nullable=True, comment='最后测试时间'),
        sa.Column('last_test_result', sa.String(length=20), nullable=True, comment='最后测试结果'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('config_name', name='uq_smtp_config_name')
    )
    op.create_index('ix_smtp_configs_id', 'smtp_configs', ['id'])
    
    # 12. 创建仪器校准表（预留功能）
    op.create_table(
        'instrument_calibrations',
        sa.Column('id', sa.Integer(), nullable=False, comment='记录ID'),
        sa.Column('instrument_code', sa.String(length=100), nullable=True, comment='仪器编码'),
        sa.Column('instrument_name', sa.String(length=255), nullable=True, comment='仪器名称'),
        sa.Column('calibration_date', sa.Date(), nullable=True, comment='校准日期'),
        sa.Column('next_calibration_date', sa.Date(), nullable=True, comment='下次校准日期'),
        sa.Column('calibration_status', sa.String(length=20), nullable=True, comment='校准状态'),
        sa.Column('calibration_certificate_path', sa.String(length=500), nullable=True, comment='校准证书路径'),
        sa.Column('responsible_user_id', sa.Integer(), nullable=True, comment='责任人ID'),
        sa.Column('msa_report_path', sa.String(length=500), nullable=True, comment='MSA报告路径'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("calibration_status IS NULL OR calibration_status IN ('valid', 'expired', 'frozen')", name='check_calibration_status')
    )
    op.create_index('ix_instrument_calibrations_id', 'instrument_calibrations', ['id'])
    op.create_index('ix_instrument_calibrations_instrument_code', 'instrument_calibrations', ['instrument_code'])
    op.create_index('ix_instrument_calibrations_next_date', 'instrument_calibrations', ['next_calibration_date'])
    
    # 13. 创建质量成本表（预留功能）
    op.create_table(
        'quality_costs',
        sa.Column('id', sa.Integer(), nullable=False, comment='成本记录ID'),
        sa.Column('cost_type', sa.String(length=50), nullable=True, comment='成本类型'),
        sa.Column('cost_category', sa.String(length=100), nullable=True, comment='成本细分类别'),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=True, comment='成本金额'),
        sa.Column('currency', sa.String(length=10), nullable=True, server_default='CNY', comment='货币单位'),
        sa.Column('related_business_type', sa.String(length=50), nullable=True, comment='关联业务类型'),
        sa.Column('related_business_id', sa.Integer(), nullable=True, comment='关联业务对象ID'),
        sa.Column('supplier_id', sa.Integer(), nullable=True, comment='关联供应商ID'),
        sa.Column('product_id', sa.Integer(), nullable=True, comment='关联产品ID'),
        sa.Column('occurred_date', sa.Date(), nullable=True, comment='成本发生日期'),
        sa.Column('description', sa.Text(), nullable=True, comment='成本描述'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("cost_type IS NULL OR cost_type IN ('internal_failure', 'external_failure', 'appraisal', 'prevention')", name='check_cost_type')
    )
    op.create_index('ix_quality_costs_id', 'quality_costs', ['id'])
    op.create_index('ix_quality_costs_occurred_date', 'quality_costs', ['occurred_date'])
    op.create_index('ix_quality_costs_supplier_id', 'quality_costs', ['supplier_id'])


def downgrade() -> None:
    """
    降级数据库架构
    删除所有表（仅用于开发环境回滚）
    
    注意：生产环境禁止执行 downgrade 操作
    """
    op.drop_table('quality_costs')
    op.drop_table('instrument_calibrations')
    op.drop_table('smtp_configs')
    op.drop_table('notification_rules')
    op.drop_table('system_configs')
    op.drop_table('feature_flags')
    op.drop_table('operation_logs')
    op.drop_table('announcement_read_logs')
    op.drop_table('announcements')
    op.drop_table('notifications')
    op.drop_table('permissions')
    op.drop_table('users')
    op.drop_table('suppliers')
