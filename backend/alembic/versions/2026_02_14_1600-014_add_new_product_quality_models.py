"""014_add_new_product_quality_models

Revision ID: 014_add_new_product_quality_models
Revises: 013_add_shipment_data_table
Create Date: 2026-02-14 16:00:00.000000

添加新品质量管理模块数据模型：
- lesson_learned_library: 经验教训库表
- new_product_projects: 新品项目表
- project_lesson_checks: 项目经验教训点检表
- stage_reviews: 阶段评审表
- trial_productions: 试产记录表
- trial_issues: 试产问题表
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '014_add_new_product_quality_models'
down_revision = '013_add_shipment_data_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    升级数据库：创建新品质量管理相关表
    遵循非破坏性原则：所有新增字段均为 nullable 或带有默认值
    """
    
    # 1. 创建经验教训库表
    op.create_table(
        'lesson_learned_library',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('lesson_title', sa.String(length=200), nullable=False, comment='经验教训标题'),
        sa.Column('lesson_content', sa.Text(), nullable=False, comment='经验教训详细内容'),
        sa.Column('source_module', sa.Enum('supplier_quality', 'process_quality', 'customer_quality', 'manual', name='sourcemodule'), nullable=False, comment='来源模块'),
        sa.Column('source_record_id', sa.Integer(), nullable=True, comment='来源记录ID（8D报告ID等）'),
        sa.Column('root_cause', sa.Text(), nullable=False, comment='根本原因'),
        sa.Column('preventive_action', sa.Text(), nullable=False, comment='预防措施'),
        sa.Column('applicable_scenarios', sa.Text(), nullable=True, comment='适用场景描述'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='是否启用'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.Column('updated_by', sa.Integer(), nullable=True, comment='更新人ID'),
        sa.PrimaryKeyConstraint('id'),
        comment='经验教训库表 - 用于新品项目的经验教训反向注入'
    )
    op.create_index('ix_lesson_learned_library_id', 'lesson_learned_library', ['id'], unique=False)
    op.create_index('ix_lesson_learned_library_is_active', 'lesson_learned_library', ['is_active'], unique=False)
    
    # 2. 创建新品项目表
    op.create_table(
        'new_product_projects',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('project_code', sa.String(length=50), nullable=False, comment='项目代码'),
        sa.Column('project_name', sa.String(length=200), nullable=False, comment='项目名称'),
        sa.Column('product_type', sa.String(length=100), nullable=True, comment='产品类型'),
        sa.Column('project_manager', sa.String(length=100), nullable=True, comment='项目经理'),
        sa.Column('project_manager_id', sa.Integer(), nullable=True, comment='项目经理用户ID'),
        sa.Column('current_stage', sa.Enum('concept', 'design', 'development', 'validation', 'trial_production', 'sop', 'closed', name='projectstage'), nullable=False, server_default='concept', comment='当前阶段'),
        sa.Column('status', sa.Enum('active', 'on_hold', 'completed', 'cancelled', name='projectstatus'), nullable=False, server_default='active', comment='项目状态'),
        sa.Column('planned_sop_date', sa.DateTime(), nullable=True, comment='计划SOP日期'),
        sa.Column('actual_sop_date', sa.DateTime(), nullable=True, comment='实际SOP日期'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.Column('updated_by', sa.Integer(), nullable=True, comment='更新人ID'),
        sa.PrimaryKeyConstraint('id'),
        comment='新品项目表 - 管理新品开发项目的全生命周期'
    )
    op.create_index('ix_new_product_projects_id', 'new_product_projects', ['id'], unique=False)
    op.create_index('ix_new_product_projects_project_code', 'new_product_projects', ['project_code'], unique=True)
    op.create_index('ix_new_product_projects_current_stage', 'new_product_projects', ['current_stage'], unique=False)
    op.create_index('ix_new_product_projects_status', 'new_product_projects', ['status'], unique=False)
    
    # 3. 创建项目经验教训点检表
    op.create_table(
        'project_lesson_checks',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('project_id', sa.Integer(), nullable=False, comment='项目ID'),
        sa.Column('lesson_id', sa.Integer(), nullable=False, comment='经验教训ID'),
        sa.Column('is_applicable', sa.Boolean(), nullable=False, comment='是否适用于本项目'),
        sa.Column('reason_if_not', sa.Text(), nullable=True, comment='不适用原因说明'),
        sa.Column('evidence_file_path', sa.String(length=500), nullable=True, comment='规避证据文件路径（设计截图、文件修改记录等）'),
        sa.Column('evidence_description', sa.Text(), nullable=True, comment='规避措施描述'),
        sa.Column('checked_by', sa.Integer(), nullable=True, comment='点检人ID'),
        sa.Column('checked_at', sa.DateTime(), nullable=True, comment='点检时间'),
        sa.Column('verified_by', sa.Integer(), nullable=True, comment='验证人ID（阶段评审员）'),
        sa.Column('verified_at', sa.DateTime(), nullable=True, comment='验证时间'),
        sa.Column('verification_result', sa.String(length=20), nullable=True, comment='验证结果：passed/failed'),
        sa.Column('verification_comment', sa.Text(), nullable=True, comment='验证意见'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.ForeignKeyConstraint(['project_id'], ['new_product_projects.id'], ),
        sa.ForeignKeyConstraint(['lesson_id'], ['lesson_learned_library.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='项目经验教训点检表 - 记录新品项目对历史经验教训的点检情况'
    )
    op.create_index('ix_project_lesson_checks_id', 'project_lesson_checks', ['id'], unique=False)
    op.create_index('ix_project_lesson_checks_project_id', 'project_lesson_checks', ['project_id'], unique=False)
    op.create_index('ix_project_lesson_checks_lesson_id', 'project_lesson_checks', ['lesson_id'], unique=False)
    
    # 4. 创建阶段评审表
    op.create_table(
        'stage_reviews',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('project_id', sa.Integer(), nullable=False, comment='项目ID'),
        sa.Column('stage_name', sa.String(length=100), nullable=False, comment='阶段名称（如：概念评审、设计评审、试产评审）'),
        sa.Column('review_date', sa.DateTime(), nullable=True, comment='评审日期'),
        sa.Column('planned_review_date', sa.DateTime(), nullable=True, comment='计划评审日期'),
        sa.Column('deliverables', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='交付物清单（JSON格式）'),
        sa.Column('review_result', sa.Enum('passed', 'conditional_pass', 'failed', 'pending', name='reviewresult'), nullable=False, server_default='pending', comment='评审结果'),
        sa.Column('review_comments', sa.Text(), nullable=True, comment='评审意见'),
        sa.Column('reviewer_ids', sa.String(length=500), nullable=True, comment='评审人ID列表（逗号分隔）'),
        sa.Column('conditional_requirements', sa.Text(), nullable=True, comment='有条件通过时的整改要求'),
        sa.Column('conditional_deadline', sa.DateTime(), nullable=True, comment='整改截止日期'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.ForeignKeyConstraint(['project_id'], ['new_product_projects.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='阶段评审表 - 新品项目的质量阀门管理'
    )
    op.create_index('ix_stage_reviews_id', 'stage_reviews', ['id'], unique=False)
    op.create_index('ix_stage_reviews_project_id', 'stage_reviews', ['project_id'], unique=False)
    
    # 5. 创建试产记录表
    op.create_table(
        'trial_productions',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('project_id', sa.Integer(), nullable=False, comment='项目ID'),
        sa.Column('work_order', sa.String(length=100), nullable=False, comment='IMS工单号'),
        sa.Column('trial_batch', sa.String(length=50), nullable=True, comment='试产批次号'),
        sa.Column('trial_date', sa.DateTime(), nullable=True, comment='试产日期'),
        sa.Column('target_metrics', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='目标指标（JSON格式）'),
        sa.Column('actual_metrics', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='实绩指标（JSON格式）'),
        sa.Column('ims_sync_status', sa.String(length=20), nullable=True, comment='IMS数据同步状态：pending/synced/failed'),
        sa.Column('ims_sync_at', sa.DateTime(), nullable=True, comment='IMS数据同步时间'),
        sa.Column('ims_sync_error', sa.Text(), nullable=True, comment='IMS同步错误信息'),
        sa.Column('status', sa.Enum('planned', 'in_progress', 'completed', 'cancelled', name='trialstatus'), nullable=False, server_default='planned', comment='试产状态'),
        sa.Column('summary_report_path', sa.String(length=500), nullable=True, comment='试产总结报告路径（Excel/PDF）'),
        sa.Column('summary_comments', sa.Text(), nullable=True, comment='试产总结评价'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.Column('updated_by', sa.Integer(), nullable=True, comment='更新人ID'),
        sa.ForeignKeyConstraint(['project_id'], ['new_product_projects.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='试产记录表 - 试产目标与实绩管理'
    )
    op.create_index('ix_trial_productions_id', 'trial_productions', ['id'], unique=False)
    op.create_index('ix_trial_productions_project_id', 'trial_productions', ['project_id'], unique=False)
    op.create_index('ix_trial_productions_work_order', 'trial_productions', ['work_order'], unique=False)
    op.create_index('ix_trial_productions_status', 'trial_productions', ['status'], unique=False)
    
    # 6. 创建试产问题表
    op.create_table(
        'trial_issues',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('trial_id', sa.Integer(), nullable=False, comment='试产记录ID'),
        sa.Column('issue_number', sa.String(length=50), nullable=True, comment='问题编号'),
        sa.Column('issue_description', sa.Text(), nullable=False, comment='问题描述'),
        sa.Column('issue_type', sa.Enum('design', 'tooling', 'process', 'material', 'equipment', 'other', name='issuetype'), nullable=False, comment='问题类型'),
        sa.Column('assigned_to', sa.Integer(), nullable=True, comment='责任人ID'),
        sa.Column('assigned_dept', sa.String(length=100), nullable=True, comment='责任部门'),
        sa.Column('root_cause', sa.Text(), nullable=True, comment='根本原因'),
        sa.Column('solution', sa.Text(), nullable=True, comment='解决方案'),
        sa.Column('solution_file_path', sa.String(length=500), nullable=True, comment='对策附件路径'),
        sa.Column('verification_method', sa.Text(), nullable=True, comment='验证方法'),
        sa.Column('verification_result', sa.String(length=20), nullable=True, comment='验证结果：passed/failed'),
        sa.Column('verified_by', sa.Integer(), nullable=True, comment='验证人ID'),
        sa.Column('verified_at', sa.DateTime(), nullable=True, comment='验证时间'),
        sa.Column('status', sa.Enum('open', 'in_progress', 'resolved', 'closed', 'escalated', name='issuestatus'), nullable=False, server_default='open', comment='问题状态'),
        sa.Column('is_escalated_to_8d', sa.Boolean(), nullable=False, server_default='false', comment='是否已升级为8D报告'),
        sa.Column('eight_d_id', sa.Integer(), nullable=True, comment='关联的8D报告ID'),
        sa.Column('escalated_at', sa.DateTime(), nullable=True, comment='升级时间'),
        sa.Column('escalation_reason', sa.Text(), nullable=True, comment='升级原因'),
        sa.Column('is_legacy_issue', sa.Boolean(), nullable=False, server_default='false', comment='是否为遗留问题'),
        sa.Column('legacy_approval_status', sa.String(length=20), nullable=True, comment='带病量产审批状态：pending/approved/rejected'),
        sa.Column('legacy_approval_by', sa.Integer(), nullable=True, comment='特批人ID'),
        sa.Column('legacy_approval_at', sa.DateTime(), nullable=True, comment='特批时间'),
        sa.Column('risk_acknowledgement_path', sa.String(length=500), nullable=True, comment='风险告知书路径'),
        sa.Column('deadline', sa.DateTime(), nullable=True, comment='要求完成时间'),
        sa.Column('resolved_at', sa.DateTime(), nullable=True, comment='解决时间'),
        sa.Column('closed_at', sa.DateTime(), nullable=True, comment='关闭时间'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.ForeignKeyConstraint(['trial_id'], ['trial_productions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='试产问题表 - 试产过程中发现的问题跟进'
    )
    op.create_index('ix_trial_issues_id', 'trial_issues', ['id'], unique=False)
    op.create_index('ix_trial_issues_trial_id', 'trial_issues', ['trial_id'], unique=False)
    op.create_index('ix_trial_issues_issue_number', 'trial_issues', ['issue_number'], unique=False)
    op.create_index('ix_trial_issues_status', 'trial_issues', ['status'], unique=False)


def downgrade() -> None:
    """
    降级数据库：删除新品质量管理相关表
    注意：生产环境禁止执行此操作
    """
    op.drop_index('ix_trial_issues_status', table_name='trial_issues')
    op.drop_index('ix_trial_issues_issue_number', table_name='trial_issues')
    op.drop_index('ix_trial_issues_trial_id', table_name='trial_issues')
    op.drop_index('ix_trial_issues_id', table_name='trial_issues')
    op.drop_table('trial_issues')
    
    op.drop_index('ix_trial_productions_status', table_name='trial_productions')
    op.drop_index('ix_trial_productions_work_order', table_name='trial_productions')
    op.drop_index('ix_trial_productions_project_id', table_name='trial_productions')
    op.drop_index('ix_trial_productions_id', table_name='trial_productions')
    op.drop_table('trial_productions')
    
    op.drop_index('ix_stage_reviews_project_id', table_name='stage_reviews')
    op.drop_index('ix_stage_reviews_id', table_name='stage_reviews')
    op.drop_table('stage_reviews')
    
    op.drop_index('ix_project_lesson_checks_lesson_id', table_name='project_lesson_checks')
    op.drop_index('ix_project_lesson_checks_project_id', table_name='project_lesson_checks')
    op.drop_index('ix_project_lesson_checks_id', table_name='project_lesson_checks')
    op.drop_table('project_lesson_checks')
    
    op.drop_index('ix_new_product_projects_status', table_name='new_product_projects')
    op.drop_index('ix_new_product_projects_current_stage', table_name='new_product_projects')
    op.drop_index('ix_new_product_projects_project_code', table_name='new_product_projects')
    op.drop_index('ix_new_product_projects_id', table_name='new_product_projects')
    op.drop_table('new_product_projects')
    
    op.drop_index('ix_lesson_learned_library_is_active', table_name='lesson_learned_library')
    op.drop_index('ix_lesson_learned_library_id', table_name='lesson_learned_library')
    op.drop_table('lesson_learned_library')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS issuestatus')
    op.execute('DROP TYPE IF EXISTS issuetype')
    op.execute('DROP TYPE IF EXISTS trialstatus')
    op.execute('DROP TYPE IF EXISTS reviewresult')
    op.execute('DROP TYPE IF EXISTS projectstatus')
    op.execute('DROP TYPE IF EXISTS projectstage')
    op.execute('DROP TYPE IF EXISTS sourcemodule')
