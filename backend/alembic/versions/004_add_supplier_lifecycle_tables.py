"""Add supplier lifecycle management tables

Revision ID: 004
Revises: 003
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # ==================== 供应商资质文件表 ====================
    op.create_table(
        'supplier_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('document_type', sa.String(length=50), nullable=False, comment='文件类型'),
        sa.Column('document_name', sa.String(length=255), nullable=False, comment='文件名称'),
        sa.Column('file_path', sa.String(length=500), nullable=False, comment='文件存储路径'),
        sa.Column('file_size', sa.Integer(), nullable=True, comment='文件大小(字节)'),
        sa.Column('issue_date', sa.DateTime(), nullable=True, comment='签发日期'),
        sa.Column('expiry_date', sa.DateTime(), nullable=True, comment='到期日期'),
        sa.Column('review_status', sa.String(length=20), nullable=False, server_default='pending', comment='审核状态'),
        sa.Column('review_comment', sa.Text(), nullable=True, comment='审核意见'),
        sa.Column('reviewed_by', sa.Integer(), nullable=True, comment='审核人ID'),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True, comment='审核时间'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('uploaded_by', sa.Integer(), nullable=True, comment='上传人ID'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='供应商资质文件表'
    )
    op.create_index('ix_supplier_documents_supplier_id', 'supplier_documents', ['supplier_id'])
    op.create_index('ix_supplier_documents_expiry_date', 'supplier_documents', ['expiry_date'])
    
    # ==================== 供应商变更管理表 ====================
    op.create_table(
        'supplier_pcns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pcn_number', sa.String(length=50), nullable=False, comment='PCN编号'),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('change_type', sa.String(length=50), nullable=False, comment='变更类型'),
        sa.Column('material_code', sa.String(length=100), nullable=True, comment='物料编码'),
        sa.Column('change_description', sa.Text(), nullable=False, comment='变更描述'),
        sa.Column('change_reason', sa.Text(), nullable=False, comment='变更原因'),
        sa.Column('impact_assessment', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='影响评估数据'),
        sa.Column('risk_level', sa.String(length=20), nullable=True, comment='风险等级'),
        sa.Column('planned_implementation_date', sa.DateTime(), nullable=True, comment='计划实施日期'),
        sa.Column('actual_implementation_date', sa.DateTime(), nullable=True, comment='实际实施日期'),
        sa.Column('cutoff_info', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='断点信息'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='submitted', comment='状态'),
        sa.Column('current_reviewer_id', sa.Integer(), nullable=True, comment='当前审核人ID'),
        sa.Column('review_comments', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='审核意见记录'),
        sa.Column('approved_by', sa.Integer(), nullable=True, comment='批准人ID'),
        sa.Column('approved_at', sa.DateTime(), nullable=True, comment='批准时间'),
        sa.Column('attachments', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='附件列表'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('submitted_by', sa.Integer(), nullable=True, comment='提交人ID'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('pcn_number'),
        comment='供应商变更管理表'
    )
    op.create_index('ix_supplier_pcns_pcn_number', 'supplier_pcns', ['pcn_number'])
    op.create_index('ix_supplier_pcns_supplier_id', 'supplier_pcns', ['supplier_id'])
    op.create_index('ix_supplier_pcns_status', 'supplier_pcns', ['status'])
    
    # ==================== 供应商审核计划表 ====================
    op.create_table(
        'supplier_audit_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('audit_year', sa.Integer(), nullable=False, comment='审核年度'),
        sa.Column('audit_month', sa.Integer(), nullable=False, comment='计划审核月份'),
        sa.Column('audit_type', sa.String(length=50), nullable=False, comment='审核类型'),
        sa.Column('auditor_id', sa.Integer(), nullable=False, comment='审核员ID'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='planned', comment='状态'),
        sa.Column('notes', sa.Text(), nullable=True, comment='备注'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='供应商审核计划表'
    )
    op.create_index('ix_supplier_audit_plans_supplier_id', 'supplier_audit_plans', ['supplier_id'])
    op.create_index('ix_supplier_audit_plans_audit_year', 'supplier_audit_plans', ['audit_year'])
    op.create_index('ix_supplier_audit_plans_status', 'supplier_audit_plans', ['status'])
    
    # ==================== 供应商审核记录表 ====================
    op.create_table(
        'supplier_audits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('audit_plan_id', sa.Integer(), nullable=True),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('audit_number', sa.String(length=50), nullable=False, comment='审核编号'),
        sa.Column('audit_type', sa.String(length=50), nullable=False, comment='审核类型'),
        sa.Column('audit_date', sa.DateTime(), nullable=False, comment='审核日期'),
        sa.Column('auditor_id', sa.Integer(), nullable=False, comment='主审核员ID'),
        sa.Column('audit_team', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='审核组成员'),
        sa.Column('audit_result', sa.String(length=20), nullable=False, comment='审核结果'),
        sa.Column('score', sa.Integer(), nullable=True, comment='审核得分'),
        sa.Column('nc_major_count', sa.Integer(), nullable=False, server_default='0', comment='严重不符合项数量'),
        sa.Column('nc_minor_count', sa.Integer(), nullable=False, server_default='0', comment='一般不符合项数量'),
        sa.Column('nc_observation_count', sa.Integer(), nullable=False, server_default='0', comment='观察项数量'),
        sa.Column('audit_report_path', sa.String(length=500), nullable=True, comment='审核报告路径'),
        sa.Column('summary', sa.Text(), nullable=True, comment='审核总结'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='completed', comment='状态'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.ForeignKeyConstraint(['audit_plan_id'], ['supplier_audit_plans.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('audit_number'),
        comment='供应商审核记录表'
    )
    op.create_index('ix_supplier_audits_audit_number', 'supplier_audits', ['audit_number'])
    op.create_index('ix_supplier_audits_audit_plan_id', 'supplier_audits', ['audit_plan_id'])
    op.create_index('ix_supplier_audits_supplier_id', 'supplier_audits', ['supplier_id'])
    op.create_index('ix_supplier_audits_audit_date', 'supplier_audits', ['audit_date'])
    
    # ==================== 供应商审核不符合项表 ====================
    op.create_table(
        'supplier_audit_ncs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('audit_id', sa.Integer(), nullable=False),
        sa.Column('nc_number', sa.String(length=50), nullable=False, comment='NC编号'),
        sa.Column('nc_type', sa.String(length=20), nullable=False, comment='NC类型'),
        sa.Column('nc_item', sa.String(length=255), nullable=False, comment='不符合条款'),
        sa.Column('nc_description', sa.Text(), nullable=False, comment='不符合描述'),
        sa.Column('evidence_photos', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='证据照片列表'),
        sa.Column('responsible_dept', sa.String(length=100), nullable=True, comment='责任部门'),
        sa.Column('assigned_to', sa.Integer(), nullable=True, comment='指派给'),
        sa.Column('root_cause', sa.Text(), nullable=True, comment='根本原因'),
        sa.Column('corrective_action', sa.Text(), nullable=True, comment='纠正措施'),
        sa.Column('corrective_evidence', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='整改证据'),
        sa.Column('verification_status', sa.String(length=20), nullable=False, server_default='open', comment='验证状态'),
        sa.Column('verified_by', sa.Integer(), nullable=True, comment='验证人ID'),
        sa.Column('verified_at', sa.DateTime(), nullable=True, comment='验证时间'),
        sa.Column('verification_comment', sa.Text(), nullable=True, comment='验证意见'),
        sa.Column('deadline', sa.DateTime(), nullable=True, comment='整改期限'),
        sa.Column('closed_at', sa.DateTime(), nullable=True, comment='关闭时间'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.ForeignKeyConstraint(['audit_id'], ['supplier_audits.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nc_number'),
        comment='供应商审核不符合项表'
    )
    op.create_index('ix_supplier_audit_ncs_nc_number', 'supplier_audit_ncs', ['nc_number'])
    op.create_index('ix_supplier_audit_ncs_audit_id', 'supplier_audit_ncs', ['audit_id'])
    op.create_index('ix_supplier_audit_ncs_assigned_to', 'supplier_audit_ncs', ['assigned_to'])
    op.create_index('ix_supplier_audit_ncs_verification_status', 'supplier_audit_ncs', ['verification_status'])
    op.create_index('ix_supplier_audit_ncs_deadline', 'supplier_audit_ncs', ['deadline'])


def downgrade():
    # Drop tables in reverse order
    op.drop_table('supplier_audit_ncs')
    op.drop_table('supplier_audits')
    op.drop_table('supplier_audit_plans')
    op.drop_table('supplier_pcns')
    op.drop_table('supplier_documents')
