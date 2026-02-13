"""Add supplier quality management models

Revision ID: 003
Revises: 002
Create Date: 2026-02-13 10:00:00.000000

本迁移脚本创建供应商质量管理相关表：
- scars: SCAR单（供应商纠正措施请求）
- eight_d_reports: 8D报告
- supplier_audits: 供应商审核记录
- supplier_performances: 供应商绩效评价
- supplier_targets: 供应商质量目标
- ppap_submissions: PPAP提交记录
- inspection_specs: 物料检验规范
- barcode_validations: 条码校验规则
- barcode_scan_records: 条码扫描记录

所有新增字段均设置为 Nullable 或带有 Default Value，
遵循双轨发布的非破坏性迁移原则。
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    升级数据库架构
    创建供应商质量管理相关表
    """
    
    # 1. 创建SCAR表（供应商纠正措施请求）
    op.create_table(
        'scars',
        sa.Column('id', sa.Integer(), nullable=False, comment='SCAR ID'),
        sa.Column('scar_number', sa.String(length=50), nullable=False, comment='SCAR单号'),
        sa.Column('supplier_id', sa.Integer(), nullable=False, comment='供应商ID'),
        sa.Column('material_code', sa.String(length=100), nullable=False, comment='物料编码'),
        sa.Column('defect_description', sa.Text(), nullable=False, comment='缺陷描述'),
        sa.Column('defect_qty', sa.Integer(), nullable=False, comment='不良数量'),
        sa.Column('severity', sa.String(length=20), nullable=False, comment='严重度'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='open', comment='状态'),
        sa.Column('current_handler_id', sa.Integer(), nullable=True, comment='当前处理人ID'),
        sa.Column('deadline', sa.DateTime(), nullable=False, comment='截止日期'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.Column('updated_by', sa.Integer(), nullable=True, comment='更新人ID'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['current_handler_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "severity IN ('low', 'medium', 'high', 'critical')",
            name='check_scar_severity'
        ),
        sa.CheckConstraint(
            "status IN ('open', 'supplier_responding', 'under_review', 'rejected', 'approved', 'closed')",
            name='check_scar_status'
        )
    )
    op.create_index('ix_scars_id', 'scars', ['id'])
    op.create_index('ix_scars_scar_number', 'scars', ['scar_number'], unique=True)
    op.create_index('ix_scars_supplier_id', 'scars', ['supplier_id'])
    op.create_index('ix_scars_material_code', 'scars', ['material_code'])
    op.create_index('ix_scars_severity', 'scars', ['severity'])
    op.create_index('ix_scars_status', 'scars', ['status'])
    op.create_index('ix_scars_current_handler_id', 'scars', ['current_handler_id'])
    op.create_index('ix_scars_deadline', 'scars', ['deadline'])

    
    # 2. 创建8D报告表
    op.create_table(
        'eight_d_reports',
        sa.Column('id', sa.Integer(), nullable=False, comment='8D报告ID'),
        sa.Column('scar_id', sa.Integer(), nullable=False, comment='关联的SCAR ID'),
        sa.Column('d0_d3_data', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='D0-D3阶段数据'),
        sa.Column('d4_d7_data', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='D4-D7阶段数据'),
        sa.Column('d8_data', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='D8阶段数据'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft', comment='状态'),
        sa.Column('submitted_by', sa.Integer(), nullable=True, comment='提交人ID'),
        sa.Column('reviewed_by', sa.Integer(), nullable=True, comment='审核人ID'),
        sa.Column('review_comments', sa.Text(), nullable=True, comment='审核意见'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('submitted_at', sa.DateTime(), nullable=True, comment='提交时间'),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True, comment='审核时间'),
        sa.ForeignKeyConstraint(['scar_id'], ['scars.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['submitted_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('scar_id', name='uq_eight_d_scar_id'),
        sa.CheckConstraint(
            "status IN ('draft', 'submitted', 'under_review', 'rejected', 'approved', 'closed')",
            name='check_eight_d_status'
        )
    )
    op.create_index('ix_eight_d_reports_id', 'eight_d_reports', ['id'])
    op.create_index('ix_eight_d_reports_scar_id', 'eight_d_reports', ['scar_id'], unique=True)
    op.create_index('ix_eight_d_reports_status', 'eight_d_reports', ['status'])

    
    # 3. 创建供应商审核表
    op.create_table(
        'supplier_audits',
        sa.Column('id', sa.Integer(), nullable=False, comment='审核ID'),
        sa.Column('supplier_id', sa.Integer(), nullable=False, comment='供应商ID'),
        sa.Column('audit_type', sa.String(length=20), nullable=False, comment='审核类型'),
        sa.Column('audit_date', sa.Date(), nullable=False, comment='审核日期'),
        sa.Column('auditor_id', sa.Integer(), nullable=False, comment='审核员ID'),
        sa.Column('audit_result', sa.String(length=20), nullable=False, comment='审核结果'),
        sa.Column('score', sa.Integer(), nullable=True, comment='审核得分'),
        sa.Column('nc_items', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='不符合项清单'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.Column('updated_by', sa.Integer(), nullable=True, comment='更新人ID'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['auditor_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "audit_type IN ('system', 'process', 'product', 'qualification', 'annual')",
            name='check_audit_type'
        ),
        sa.CheckConstraint(
            "audit_result IN ('passed', 'conditional', 'failed')",
            name='check_audit_result'
        )
    )
    op.create_index('ix_supplier_audits_id', 'supplier_audits', ['id'])
    op.create_index('ix_supplier_audits_supplier_id', 'supplier_audits', ['supplier_id'])
    op.create_index('ix_supplier_audits_audit_type', 'supplier_audits', ['audit_type'])
    op.create_index('ix_supplier_audits_audit_date', 'supplier_audits', ['audit_date'])

    
    # 4. 创建供应商绩效评价表
    op.create_table(
        'supplier_performances',
        sa.Column('id', sa.Integer(), nullable=False, comment='绩效ID'),
        sa.Column('supplier_id', sa.Integer(), nullable=False, comment='供应商ID'),
        sa.Column('month', sa.String(length=7), nullable=False, comment='评价月份'),
        sa.Column('incoming_quality_score', sa.Float(), nullable=False, comment='来料质量得分'),
        sa.Column('process_quality_score', sa.Float(), nullable=False, comment='制程质量得分'),
        sa.Column('cooperation_score', sa.Float(), nullable=False, comment='配合度得分'),
        sa.Column('customer_quality_deduction', sa.Float(), nullable=False, server_default='0.0', comment='客户质量扣分'),
        sa.Column('final_score', sa.Float(), nullable=False, comment='最终得分'),
        sa.Column('grade', sa.String(length=1), nullable=False, comment='绩效等级'),
        sa.Column('is_reviewed', sa.Boolean(), nullable=False, server_default='false', comment='是否已人工校核'),
        sa.Column('reviewed_by', sa.Integer(), nullable=True, comment='校核人ID'),
        sa.Column('review_notes', sa.String(length=500), nullable=True, comment='校核备注'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "grade IN ('A', 'B', 'C', 'D')",
            name='check_performance_grade'
        )
    )
    op.create_index('ix_supplier_performances_id', 'supplier_performances', ['id'])
    op.create_index('ix_supplier_performances_supplier_id', 'supplier_performances', ['supplier_id'])
    op.create_index('ix_supplier_performances_month', 'supplier_performances', ['month'])
    op.create_index('ix_supplier_performances_grade', 'supplier_performances', ['grade'])
    op.create_index('ix_supplier_performances_supplier_month', 'supplier_performances', ['supplier_id', 'month'], unique=True)

    
    # 5. 创建供应商质量目标表
    op.create_table(
        'supplier_targets',
        sa.Column('id', sa.Integer(), nullable=False, comment='目标ID'),
        sa.Column('supplier_id', sa.Integer(), nullable=False, comment='供应商ID'),
        sa.Column('year', sa.Integer(), nullable=False, comment='目标年份'),
        sa.Column('target_type', sa.String(length=30), nullable=False, comment='目标类型'),
        sa.Column('target_value', sa.Float(), nullable=False, comment='目标值'),
        sa.Column('is_individual', sa.Boolean(), nullable=False, server_default='false', comment='是否单独设定'),
        sa.Column('is_signed', sa.Boolean(), nullable=False, server_default='false', comment='是否已签署'),
        sa.Column('signed_at', sa.DateTime(), nullable=True, comment='签署时间'),
        sa.Column('signed_by', sa.Integer(), nullable=True, comment='签署人ID'),
        sa.Column('is_approved', sa.Boolean(), nullable=False, server_default='false', comment='是否已审批'),
        sa.Column('approved_by', sa.Integer(), nullable=True, comment='审批人ID'),
        sa.Column('approved_at', sa.DateTime(), nullable=True, comment='审批时间'),
        sa.Column('previous_year_actual', sa.Float(), nullable=True, comment='上一年实际达成值'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.Column('updated_by', sa.Integer(), nullable=True, comment='更新人ID'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['signed_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "target_type IN ('incoming_pass_rate', 'material_ppm', 'process_defect_rate', 'zero_km_ppm', 'mis_3_ppm', 'mis_12_ppm')",
            name='check_target_type'
        )
    )
    op.create_index('ix_supplier_targets_id', 'supplier_targets', ['id'])
    op.create_index('ix_supplier_targets_supplier_id', 'supplier_targets', ['supplier_id'])
    op.create_index('ix_supplier_targets_year', 'supplier_targets', ['year'])
    op.create_index('ix_supplier_targets_target_type', 'supplier_targets', ['target_type'])
    op.create_index('ix_supplier_targets_is_signed', 'supplier_targets', ['is_signed'])
    op.create_index('ix_supplier_targets_supplier_year_type', 'supplier_targets', ['supplier_id', 'year', 'target_type'], unique=True)

    
    # 6. 创建PPAP提交表
    op.create_table(
        'ppap_submissions',
        sa.Column('id', sa.Integer(), nullable=False, comment='PPAP ID'),
        sa.Column('supplier_id', sa.Integer(), nullable=False, comment='供应商ID'),
        sa.Column('material_code', sa.String(length=100), nullable=False, comment='物料编码'),
        sa.Column('ppap_level', sa.String(length=10), nullable=False, server_default='level_3', comment='PPAP提交等级'),
        sa.Column('submission_date', sa.Date(), nullable=True, comment='提交日期'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending', comment='状态'),
        sa.Column('documents', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='文件清单'),
        sa.Column('reviewer_id', sa.Integer(), nullable=True, comment='审核人ID'),
        sa.Column('review_comments', sa.String(length=1000), nullable=True, comment='审核意见'),
        sa.Column('approved_at', sa.DateTime(), nullable=True, comment='批准时间'),
        sa.Column('revalidation_due_date', sa.Date(), nullable=True, comment='再鉴定到期日期'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.Column('updated_by', sa.Integer(), nullable=True, comment='更新人ID'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "ppap_level IN ('level_1', 'level_2', 'level_3', 'level_4', 'level_5')",
            name='check_ppap_level'
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'submitted', 'under_review', 'rejected', 'approved', 'expired')",
            name='check_ppap_status'
        )
    )
    op.create_index('ix_ppap_submissions_id', 'ppap_submissions', ['id'])
    op.create_index('ix_ppap_submissions_supplier_id', 'ppap_submissions', ['supplier_id'])
    op.create_index('ix_ppap_submissions_material_code', 'ppap_submissions', ['material_code'])
    op.create_index('ix_ppap_submissions_submission_date', 'ppap_submissions', ['submission_date'])
    op.create_index('ix_ppap_submissions_status', 'ppap_submissions', ['status'])
    op.create_index('ix_ppap_submissions_revalidation_due_date', 'ppap_submissions', ['revalidation_due_date'])

    
    # 7. 创建物料检验规范表
    op.create_table(
        'inspection_specs',
        sa.Column('id', sa.Integer(), nullable=False, comment='规范ID'),
        sa.Column('material_code', sa.String(length=100), nullable=False, comment='物料编码'),
        sa.Column('supplier_id', sa.Integer(), nullable=False, comment='供应商ID'),
        sa.Column('version', sa.String(length=20), nullable=False, comment='版本号'),
        sa.Column('sip_file_path', sa.String(length=500), nullable=True, comment='SIP文件路径'),
        sa.Column('key_characteristics', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='关键检验项目'),
        sa.Column('report_frequency_type', sa.String(length=20), nullable=True, comment='报告频率类型'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft', comment='状态'),
        sa.Column('reviewer_id', sa.Integer(), nullable=True, comment='审核人ID'),
        sa.Column('review_comments', sa.String(length=1000), nullable=True, comment='审核意见'),
        sa.Column('approved_at', sa.DateTime(), nullable=True, comment='批准时间'),
        sa.Column('effective_date', sa.DateTime(), nullable=True, comment='生效日期'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.Column('updated_by', sa.Integer(), nullable=True, comment='更新人ID'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "status IN ('draft', 'pending_review', 'approved', 'archived')",
            name='check_inspection_spec_status'
        )
    )
    op.create_index('ix_inspection_specs_id', 'inspection_specs', ['id'])
    op.create_index('ix_inspection_specs_material_code', 'inspection_specs', ['material_code'])
    op.create_index('ix_inspection_specs_supplier_id', 'inspection_specs', ['supplier_id'])
    op.create_index('ix_inspection_specs_status', 'inspection_specs', ['status'])
    op.create_index('ix_inspection_specs_effective_date', 'inspection_specs', ['effective_date'])

    
    # 8. 创建条码校验规则表
    op.create_table(
        'barcode_validations',
        sa.Column('id', sa.Integer(), nullable=False, comment='校验规则ID'),
        sa.Column('material_code', sa.String(length=100), nullable=False, comment='物料编码'),
        sa.Column('validation_rules', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='校验规则'),
        sa.Column('regex_pattern', sa.String(length=200), nullable=True, comment='正则表达式'),
        sa.Column('is_unique_check', sa.Boolean(), nullable=False, server_default='false', comment='是否启用唯一性校验'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.Column('updated_by', sa.Integer(), nullable=True, comment='更新人ID'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_barcode_validations_id', 'barcode_validations', ['id'])
    op.create_index('ix_barcode_validations_material_code', 'barcode_validations', ['material_code'])
    
    # 9. 创建条码扫描记录表
    op.create_table(
        'barcode_scan_records',
        sa.Column('id', sa.Integer(), nullable=False, comment='扫描记录ID'),
        sa.Column('material_code', sa.String(length=100), nullable=False, comment='物料编码'),
        sa.Column('supplier_id', sa.Integer(), nullable=False, comment='供应商ID'),
        sa.Column('batch_number', sa.String(length=100), nullable=True, comment='批次号'),
        sa.Column('barcode_content', sa.String(length=200), nullable=False, comment='条码内容'),
        sa.Column('is_pass', sa.Boolean(), nullable=False, comment='是否通过'),
        sa.Column('error_reason', sa.String(length=500), nullable=True, comment='错误原因'),
        sa.Column('scanned_by', sa.Integer(), nullable=False, comment='扫描人ID'),
        sa.Column('scanned_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='扫描时间'),
        sa.Column('device_ip', sa.String(length=50), nullable=True, comment='设备IP'),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false', comment='是否已归档'),
        sa.Column('archived_at', sa.DateTime(), nullable=True, comment='归档时间'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['scanned_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_barcode_scan_records_id', 'barcode_scan_records', ['id'])
    op.create_index('ix_barcode_scan_records_material_code', 'barcode_scan_records', ['material_code'])
    op.create_index('ix_barcode_scan_records_supplier_id', 'barcode_scan_records', ['supplier_id'])
    op.create_index('ix_barcode_scan_records_batch_number', 'barcode_scan_records', ['batch_number'])
    op.create_index('ix_barcode_scan_records_barcode_content', 'barcode_scan_records', ['barcode_content'])
    op.create_index('ix_barcode_scan_records_is_pass', 'barcode_scan_records', ['is_pass'])
    op.create_index('ix_barcode_scan_records_scanned_at', 'barcode_scan_records', ['scanned_at'])
    op.create_index('ix_barcode_scan_records_is_archived', 'barcode_scan_records', ['is_archived'])


def downgrade() -> None:
    """
    降级数据库架构
    删除供应商质量管理相关表
    """
    # 删除表（按依赖关系逆序删除）
    op.drop_table('barcode_scan_records')
    op.drop_table('barcode_validations')
    op.drop_table('inspection_specs')
    op.drop_table('ppap_submissions')
    op.drop_table('supplier_targets')
    op.drop_table('supplier_performances')
    op.drop_table('supplier_audits')
    op.drop_table('eight_d_reports')
    op.drop_table('scars')
