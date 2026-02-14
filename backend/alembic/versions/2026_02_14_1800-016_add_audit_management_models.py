"""016_add_audit_management_models

Revision ID: 016_add_audit_management_models
Revises: 015_add_initial_flow_control_table
Create Date: 2026-02-14 18:00:00.000000

添加审核管理模块数据表：
- audit_plans: 审核计划表
- audit_templates: 审核模板表
- audit_executions: 审核执行记录表
- audit_ncs: 审核不符合项表
- customer_audits: 客户审核台账表

功能说明：
本迁移实现审核管理模块的数据模型，支持：
1. 多体系审核计划管理（IATF16949体系审核、VDA6.3过程审核、VDA6.5产品审核、客户审核）
2. 数字化检查表模板库（内置标准模板及自定义模板）
3. 在线审核执行与打分（支持移动端现场录入）
4. 不符合项（NC）整改闭环跟踪
5. 客户审核特别管理（外部问题清单对接）

Requirements: 2.9.1, 2.9.2, 2.9.3, 2.9.4
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '016_add_audit_management_models'
down_revision = '015_add_initial_flow_control_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    升级数据库：创建审核管理模块相关表
    遵循非破坏性原则：所有新增字段均为 nullable 或带有 server_default
    """
    
    # 1. 创建审核计划表
    op.create_table(
        'audit_plans',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('audit_type', sa.String(length=50), nullable=False, comment='审核类型: system_audit (IATF16949), process_audit (VDA6.3), product_audit (VDA6.5), customer_audit'),
        sa.Column('audit_name', sa.String(length=255), nullable=False, comment='审核名称'),
        sa.Column('planned_date', sa.DateTime(), nullable=False, comment='计划审核日期'),
        sa.Column('auditor_id', sa.Integer(), nullable=False, comment='主审核员ID'),
        sa.Column('auditee_dept', sa.String(length=100), nullable=False, comment='被审核部门'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='planned', comment='状态: planned, in_progress, completed, postponed, cancelled'),
        sa.Column('postpone_reason', sa.Text(), nullable=True, comment='延期原因'),
        sa.Column('postpone_approved_by', sa.Integer(), nullable=True, comment='延期批准人ID'),
        sa.Column('postpone_approved_at', sa.DateTime(), nullable=True, comment='延期批准时间'),
        sa.Column('notes', sa.Text(), nullable=True, comment='备注'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.PrimaryKeyConstraint('id'),
        comment='审核计划表 - 管理年度审核计划'
    )
    op.create_index('ix_audit_plans_id', 'audit_plans', ['id'], unique=False)
    op.create_index('ix_audit_plans_audit_type', 'audit_plans', ['audit_type'], unique=False)
    op.create_index('ix_audit_plans_planned_date', 'audit_plans', ['planned_date'], unique=False)
    op.create_index('ix_audit_plans_auditor_id', 'audit_plans', ['auditor_id'], unique=False)
    op.create_index('ix_audit_plans_status', 'audit_plans', ['status'], unique=False)
    
    # 2. 创建审核模板表
    op.create_table(
        'audit_templates',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('template_name', sa.String(length=255), nullable=False, comment='模板名称'),
        sa.Column('audit_type', sa.String(length=50), nullable=False, comment='适用审核类型: system_audit, process_audit, product_audit, custom'),
        sa.Column('checklist_items', postgresql.JSON(astext_type=sa.Text()), nullable=False, comment='检查表条款列表 (JSON格式，包含条款编号、描述、评分标准等)'),
        sa.Column('scoring_rules', postgresql.JSON(astext_type=sa.Text()), nullable=False, comment='评分规则 (JSON格式，包含评分方法、等级划分、降级规则等)'),
        sa.Column('description', sa.Text(), nullable=True, comment='模板描述'),
        sa.Column('is_builtin', sa.Boolean(), nullable=False, server_default='false', comment='是否为系统内置模板'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='是否启用'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('template_name'),
        comment='审核模板表 - 存储审核检查表模板'
    )
    op.create_index('ix_audit_templates_id', 'audit_templates', ['id'], unique=False)
    op.create_index('ix_audit_templates_template_name', 'audit_templates', ['template_name'], unique=True)
    op.create_index('ix_audit_templates_audit_type', 'audit_templates', ['audit_type'], unique=False)
    op.create_index('ix_audit_templates_is_active', 'audit_templates', ['is_active'], unique=False)
    
    # 3. 创建审核执行记录表
    op.create_table(
        'audit_executions',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('audit_plan_id', sa.Integer(), nullable=False, comment='审核计划ID'),
        sa.Column('template_id', sa.Integer(), nullable=False, comment='审核模板ID'),
        sa.Column('audit_date', sa.DateTime(), nullable=False, comment='实际审核日期'),
        sa.Column('auditor_id', sa.Integer(), nullable=False, comment='主审核员ID'),
        sa.Column('audit_team', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='审核组成员列表 (JSON格式)'),
        sa.Column('checklist_results', postgresql.JSON(astext_type=sa.Text()), nullable=False, comment='检查表结果 (JSON格式，包含每个条款的评分、证据照片等)'),
        sa.Column('final_score', sa.Integer(), nullable=True, comment='最终得分 (百分制)'),
        sa.Column('grade', sa.String(length=10), nullable=True, comment='等级评定 (A/B/C/D)'),
        sa.Column('audit_report_path', sa.String(length=500), nullable=True, comment='审核报告文件路径'),
        sa.Column('summary', sa.Text(), nullable=True, comment='审核总结'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft', comment='状态: draft, completed, nc_open, nc_closed'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.ForeignKeyConstraint(['audit_plan_id'], ['audit_plans.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['template_id'], ['audit_templates.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        comment='审核执行记录表 - 存储实际执行的审核记录'
    )
    op.create_index('ix_audit_executions_id', 'audit_executions', ['id'], unique=False)
    op.create_index('ix_audit_executions_audit_plan_id', 'audit_executions', ['audit_plan_id'], unique=False)
    op.create_index('ix_audit_executions_template_id', 'audit_executions', ['template_id'], unique=False)
    op.create_index('ix_audit_executions_audit_date', 'audit_executions', ['audit_date'], unique=False)
    op.create_index('ix_audit_executions_auditor_id', 'audit_executions', ['auditor_id'], unique=False)
    op.create_index('ix_audit_executions_status', 'audit_executions', ['status'], unique=False)
    
    # 4. 创建审核不符合项表
    op.create_table(
        'audit_ncs',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('audit_id', sa.Integer(), nullable=False, comment='审核执行记录ID'),
        sa.Column('nc_item', sa.String(length=255), nullable=False, comment='不符合条款'),
        sa.Column('nc_description', sa.Text(), nullable=False, comment='不符合描述'),
        sa.Column('evidence_photo_path', sa.String(length=500), nullable=True, comment='证据照片路径 (多个照片用逗号分隔或JSON格式)'),
        sa.Column('responsible_dept', sa.String(length=100), nullable=False, comment='责任部门'),
        sa.Column('assigned_to', sa.Integer(), nullable=True, comment='指派给(用户ID)'),
        sa.Column('root_cause', sa.Text(), nullable=True, comment='根本原因'),
        sa.Column('corrective_action', sa.Text(), nullable=True, comment='纠正措施'),
        sa.Column('corrective_evidence', sa.String(length=500), nullable=True, comment='整改证据文件路径'),
        sa.Column('verification_status', sa.String(length=20), nullable=False, server_default='open', comment='验证状态: open, submitted, verified, closed, rejected'),
        sa.Column('verified_by', sa.Integer(), nullable=True, comment='验证人ID'),
        sa.Column('verified_at', sa.DateTime(), nullable=True, comment='验证时间'),
        sa.Column('verification_comment', sa.Text(), nullable=True, comment='验证意见'),
        sa.Column('deadline', sa.DateTime(), nullable=False, comment='整改期限'),
        sa.Column('closed_at', sa.DateTime(), nullable=True, comment='关闭时间'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.ForeignKeyConstraint(['audit_id'], ['audit_executions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='审核不符合项表 - 管理审核中发现的不符合项及整改跟踪'
    )
    op.create_index('ix_audit_ncs_id', 'audit_ncs', ['id'], unique=False)
    op.create_index('ix_audit_ncs_audit_id', 'audit_ncs', ['audit_id'], unique=False)
    op.create_index('ix_audit_ncs_assigned_to', 'audit_ncs', ['assigned_to'], unique=False)
    op.create_index('ix_audit_ncs_verification_status', 'audit_ncs', ['verification_status'], unique=False)
    op.create_index('ix_audit_ncs_deadline', 'audit_ncs', ['deadline'], unique=False)
    
    # 5. 创建客户审核台账表
    op.create_table(
        'customer_audits',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('customer_name', sa.String(length=255), nullable=False, comment='客户名称'),
        sa.Column('audit_type', sa.String(length=50), nullable=False, comment='审核类型: system, process, product, qualification, potential_supplier'),
        sa.Column('audit_date', sa.DateTime(), nullable=False, comment='审核日期'),
        sa.Column('final_result', sa.String(length=50), nullable=False, comment='最终结果: passed, conditional_passed, failed, pending'),
        sa.Column('score', sa.Integer(), nullable=True, comment='审核得分 (如果客户提供)'),
        sa.Column('external_issue_list_path', sa.String(length=500), nullable=True, comment='客户提供的问题整改清单文件路径 (Excel等)'),
        sa.Column('internal_contact', sa.String(length=255), nullable=True, comment='内部接待人员'),
        sa.Column('audit_report_path', sa.String(length=500), nullable=True, comment='审核报告文件路径'),
        sa.Column('summary', sa.Text(), nullable=True, comment='审核总结'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='completed', comment='状态: completed, issue_open, issue_closed'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.PrimaryKeyConstraint('id'),
        comment='客户审核台账表 - 管理客户来厂审核的台账和问题跟踪'
    )
    op.create_index('ix_customer_audits_id', 'customer_audits', ['id'], unique=False)
    op.create_index('ix_customer_audits_customer_name', 'customer_audits', ['customer_name'], unique=False)
    op.create_index('ix_customer_audits_audit_date', 'customer_audits', ['audit_date'], unique=False)
    op.create_index('ix_customer_audits_status', 'customer_audits', ['status'], unique=False)


def downgrade() -> None:
    """
    降级数据库：删除审核管理模块相关表
    注意：生产环境禁止执行此操作
    """
    # 删除客户审核台账表
    op.drop_index('ix_customer_audits_status', table_name='customer_audits')
    op.drop_index('ix_customer_audits_audit_date', table_name='customer_audits')
    op.drop_index('ix_customer_audits_customer_name', table_name='customer_audits')
    op.drop_index('ix_customer_audits_id', table_name='customer_audits')
    op.drop_table('customer_audits')
    
    # 删除审核不符合项表
    op.drop_index('ix_audit_ncs_deadline', table_name='audit_ncs')
    op.drop_index('ix_audit_ncs_verification_status', table_name='audit_ncs')
    op.drop_index('ix_audit_ncs_assigned_to', table_name='audit_ncs')
    op.drop_index('ix_audit_ncs_audit_id', table_name='audit_ncs')
    op.drop_index('ix_audit_ncs_id', table_name='audit_ncs')
    op.drop_table('audit_ncs')
    
    # 删除审核执行记录表
    op.drop_index('ix_audit_executions_status', table_name='audit_executions')
    op.drop_index('ix_audit_executions_auditor_id', table_name='audit_executions')
    op.drop_index('ix_audit_executions_audit_date', table_name='audit_executions')
    op.drop_index('ix_audit_executions_template_id', table_name='audit_executions')
    op.drop_index('ix_audit_executions_audit_plan_id', table_name='audit_executions')
    op.drop_index('ix_audit_executions_id', table_name='audit_executions')
    op.drop_table('audit_executions')
    
    # 删除审核模板表
    op.drop_index('ix_audit_templates_is_active', table_name='audit_templates')
    op.drop_index('ix_audit_templates_audit_type', table_name='audit_templates')
    op.drop_index('ix_audit_templates_template_name', table_name='audit_templates')
    op.drop_index('ix_audit_templates_id', table_name='audit_templates')
    op.drop_table('audit_templates')
    
    # 删除审核计划表
    op.drop_index('ix_audit_plans_status', table_name='audit_plans')
    op.drop_index('ix_audit_plans_auditor_id', table_name='audit_plans')
    op.drop_index('ix_audit_plans_planned_date', table_name='audit_plans')
    op.drop_index('ix_audit_plans_audit_type', table_name='audit_plans')
    op.drop_index('ix_audit_plans_id', table_name='audit_plans')
    op.drop_table('audit_plans')
