"""Add quality data models

Revision ID: 002
Revises: 001
Create Date: 2026-02-12 14:00:00.000000

本迁移脚本创建质量数据面板相关表：
- quality_metrics: 质量指标数据表
- ims_sync_logs: IMS同步日志表

所有新增字段均设置为 Nullable 或带有 Default Value，
遵循双轨发布的非破坏性迁移原则。
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    升级数据库架构
    创建质量数据面板相关表
    """
    
    # 1. 创建质量指标表
    op.create_table(
        'quality_metrics',
        sa.Column('id', sa.Integer(), nullable=False, comment='指标ID'),
        sa.Column('metric_type', sa.String(length=50), nullable=False, comment='指标类型'),
        sa.Column('metric_date', sa.Date(), nullable=False, comment='指标日期'),
        sa.Column('value', sa.Numeric(precision=15, scale=4), nullable=False, comment='指标实际值'),
        sa.Column('target_value', sa.Numeric(precision=15, scale=4), nullable=True, comment='指标目标值'),
        sa.Column('product_type', sa.String(length=100), nullable=True, comment='产品类型'),
        sa.Column('supplier_id', sa.Integer(), nullable=True, comment='供应商ID'),
        sa.Column('line_id', sa.String(length=50), nullable=True, comment='产线ID'),
        sa.Column('process_id', sa.String(length=50), nullable=True, comment='工序ID'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "metric_type IN ('incoming_batch_pass_rate', 'material_online_ppm', 'process_defect_rate', "
            "'process_fpy', 'okm_ppm', 'mis_3_ppm', 'mis_12_ppm')",
            name='check_metric_type'
        )
    )
    
    # 创建索引以优化查询性能
    op.create_index('ix_quality_metrics_id', 'quality_metrics', ['id'])
    op.create_index('ix_quality_metrics_metric_type', 'quality_metrics', ['metric_type'])
    op.create_index('ix_quality_metrics_metric_date', 'quality_metrics', ['metric_date'])
    op.create_index('ix_quality_metrics_product_type', 'quality_metrics', ['product_type'])
    op.create_index('ix_quality_metrics_supplier_id', 'quality_metrics', ['supplier_id'])
    op.create_index('ix_quality_metrics_line_id', 'quality_metrics', ['line_id'])
    op.create_index('ix_quality_metrics_process_id', 'quality_metrics', ['process_id'])
    
    # 创建复合索引以优化常见查询场景
    op.create_index(
        'ix_quality_metrics_type_date',
        'quality_metrics',
        ['metric_type', 'metric_date'],
        unique=False
    )
    op.create_index(
        'ix_quality_metrics_type_supplier_date',
        'quality_metrics',
        ['metric_type', 'supplier_id', 'metric_date'],
        unique=False
    )
    
    # 2. 创建IMS同步日志表
    op.create_table(
        'ims_sync_logs',
        sa.Column('id', sa.Integer(), nullable=False, comment='日志ID'),
        sa.Column('sync_type', sa.String(length=50), nullable=False, comment='同步类型'),
        sa.Column('sync_date', sa.Date(), nullable=False, comment='同步日期'),
        sa.Column('status', sa.String(length=20), nullable=False, comment='同步状态'),
        sa.Column('records_count', sa.Integer(), nullable=False, server_default='0', comment='同步记录数'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),
        sa.Column('started_at', sa.DateTime(), nullable=False, comment='开始时间'),
        sa.Column('completed_at', sa.DateTime(), nullable=True, comment='完成时间'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "sync_type IN ('incoming_inspection', 'production_output', 'process_test', "
            "'process_defects', 'shipment_data', 'first_pass_test', 'iqc_results', 'special_approval')",
            name='check_sync_type'
        ),
        sa.CheckConstraint(
            "status IN ('success', 'failed', 'partial', 'in_progress')",
            name='check_sync_status'
        )
    )
    
    # 创建索引以优化查询性能
    op.create_index('ix_ims_sync_logs_id', 'ims_sync_logs', ['id'])
    op.create_index('ix_ims_sync_logs_sync_type', 'ims_sync_logs', ['sync_type'])
    op.create_index('ix_ims_sync_logs_sync_date', 'ims_sync_logs', ['sync_date'])
    op.create_index('ix_ims_sync_logs_status', 'ims_sync_logs', ['status'])
    
    # 创建复合索引以优化常见查询场景
    op.create_index(
        'ix_ims_sync_logs_type_date',
        'ims_sync_logs',
        ['sync_type', 'sync_date'],
        unique=False
    )


def downgrade() -> None:
    """
    降级数据库架构
    删除质量数据面板相关表
    """
    # 删除索引
    op.drop_index('ix_ims_sync_logs_type_date', table_name='ims_sync_logs')
    op.drop_index('ix_ims_sync_logs_status', table_name='ims_sync_logs')
    op.drop_index('ix_ims_sync_logs_sync_date', table_name='ims_sync_logs')
    op.drop_index('ix_ims_sync_logs_sync_type', table_name='ims_sync_logs')
    op.drop_index('ix_ims_sync_logs_id', table_name='ims_sync_logs')
    
    op.drop_index('ix_quality_metrics_type_supplier_date', table_name='quality_metrics')
    op.drop_index('ix_quality_metrics_type_date', table_name='quality_metrics')
    op.drop_index('ix_quality_metrics_process_id', table_name='quality_metrics')
    op.drop_index('ix_quality_metrics_line_id', table_name='quality_metrics')
    op.drop_index('ix_quality_metrics_supplier_id', table_name='quality_metrics')
    op.drop_index('ix_quality_metrics_product_type', table_name='quality_metrics')
    op.drop_index('ix_quality_metrics_metric_date', table_name='quality_metrics')
    op.drop_index('ix_quality_metrics_metric_type', table_name='quality_metrics')
    op.drop_index('ix_quality_metrics_id', table_name='quality_metrics')
    
    # 删除表
    op.drop_table('ims_sync_logs')
    op.drop_table('quality_metrics')
