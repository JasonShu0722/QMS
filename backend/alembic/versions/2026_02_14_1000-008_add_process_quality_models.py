"""Add process quality management models

Revision ID: 008
Revises: 007
Create Date: 2026-02-14 10:00:00.000000

本迁移脚本创建过程质量管理相关表：
- process_defects: 制程不良品记录
- process_issues: 制程质量问题单

所有新增字段均设置为 Nullable 或带有 Default Value，
遵循双轨发布的非破坏性迁移原则。
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    升级数据库架构
    创建过程质量管理相关表
    """
    
    # 1. 创建制程不良品表
    op.create_table(
        'process_defects',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('defect_date', sa.Date(), nullable=False, comment='不良发生日期'),
        sa.Column('work_order', sa.String(length=100), nullable=False, comment='工单号'),
        sa.Column('process_id', sa.String(length=50), nullable=False, comment='工序ID'),
        sa.Column('line_id', sa.String(length=50), nullable=False, comment='产线ID'),
        sa.Column('defect_type', sa.String(length=200), nullable=False, comment='不良类型/失效模式'),
        sa.Column('defect_qty', sa.Integer(), nullable=False, comment='不良数量'),
        sa.Column('responsibility_category', sa.String(length=50), nullable=False, comment='责任类别'),
        sa.Column('operator_id', sa.Integer(), nullable=True, comment='操作员ID'),
        sa.Column('recorded_by', sa.Integer(), nullable=False, comment='记录人ID'),
        sa.Column('material_code', sa.String(length=100), nullable=True, comment='物料编码'),
        sa.Column('supplier_id', sa.Integer(), nullable=True, comment='供应商ID'),
        sa.Column('remarks', sa.String(length=500), nullable=True, comment='备注'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.ForeignKeyConstraint(['operator_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['recorded_by'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='制程不良品记录表'
    )
    
    # 创建索引
    op.create_index('ix_process_defects_defect_date', 'process_defects', ['defect_date'])
    op.create_index('ix_process_defects_work_order', 'process_defects', ['work_order'])
    op.create_index('ix_process_defects_process_id', 'process_defects', ['process_id'])
    op.create_index('ix_process_defects_line_id', 'process_defects', ['line_id'])
    op.create_index('ix_process_defects_responsibility_category', 'process_defects', ['responsibility_category'])
    op.create_index('ix_process_defects_material_code', 'process_defects', ['material_code'])
    op.create_index('ix_process_defects_supplier_id', 'process_defects', ['supplier_id'])
    
    # 2. 创建制程质量问题单表
    op.create_table(
        'process_issues',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('issue_number', sa.String(length=50), nullable=False, comment='问题单编号'),
        sa.Column('issue_description', sa.Text(), nullable=False, comment='问题描述'),
        sa.Column('responsibility_category', sa.String(length=50), nullable=False, comment='责任类别'),
        sa.Column('assigned_to', sa.Integer(), nullable=False, comment='当前处理人ID'),
        sa.Column('root_cause', sa.Text(), nullable=True, comment='根本原因分析'),
        sa.Column('containment_action', sa.Text(), nullable=True, comment='围堵措施'),
        sa.Column('corrective_action', sa.Text(), nullable=True, comment='纠正措施'),
        sa.Column('verification_period', sa.Integer(), nullable=True, comment='验证期（天数）'),
        sa.Column('verification_start_date', sa.Date(), nullable=True, comment='验证开始日期'),
        sa.Column('verification_end_date', sa.Date(), nullable=True, comment='验证结束日期'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='open', comment='问题单状态'),
        sa.Column('related_defect_ids', sa.String(length=500), nullable=True, comment='关联的不良品记录ID'),
        sa.Column('evidence_files', sa.Text(), nullable=True, comment='改善证据附件路径（JSON格式）'),
        sa.Column('created_by', sa.Integer(), nullable=False, comment='发起人ID'),
        sa.Column('verified_by', sa.Integer(), nullable=True, comment='验证人ID'),
        sa.Column('closed_by', sa.Integer(), nullable=True, comment='关闭人ID'),
        sa.Column('closed_at', sa.DateTime(), nullable=True, comment='关闭时间'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['verified_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['closed_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('issue_number'),
        comment='制程质量问题单表'
    )
    
    # 创建索引
    op.create_index('ix_process_issues_issue_number', 'process_issues', ['issue_number'], unique=True)
    op.create_index('ix_process_issues_responsibility_category', 'process_issues', ['responsibility_category'])
    op.create_index('ix_process_issues_assigned_to', 'process_issues', ['assigned_to'])
    op.create_index('ix_process_issues_status', 'process_issues', ['status'])


def downgrade() -> None:
    """
    降级数据库架构
    删除过程质量管理相关表
    
    注意：在生产环境中，降级操作应谨慎执行，
    因为会导致数据丢失。建议仅在开发/测试环境使用。
    """
    
    # 删除索引
    op.drop_index('ix_process_issues_status', table_name='process_issues')
    op.drop_index('ix_process_issues_assigned_to', table_name='process_issues')
    op.drop_index('ix_process_issues_responsibility_category', table_name='process_issues')
    op.drop_index('ix_process_issues_issue_number', table_name='process_issues')
    
    op.drop_index('ix_process_defects_supplier_id', table_name='process_defects')
    op.drop_index('ix_process_defects_material_code', table_name='process_defects')
    op.drop_index('ix_process_defects_responsibility_category', table_name='process_defects')
    op.drop_index('ix_process_defects_line_id', table_name='process_defects')
    op.drop_index('ix_process_defects_process_id', table_name='process_defects')
    op.drop_index('ix_process_defects_work_order', table_name='process_defects')
    op.drop_index('ix_process_defects_defect_date', table_name='process_defects')
    
    # 删除表
    op.drop_table('process_issues')
    op.drop_table('process_defects')
