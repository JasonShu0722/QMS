"""add shipment data table

Revision ID: 013_add_shipment_data
Revises: 012_add_customer_quality_models
Create Date: 2026-02-14 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '013_add_shipment_data'
down_revision = '012_add_customer_quality_models'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    创建发货数据表
    
    用途：
    - 维护过去 24 个月的分月出货数据
    - 为客户质量管理模块提供 PPM 计算的分母数据
    - 支持 0KM、3MIS、12MIS 不良 PPM 计算
    
    遵循双轨兼容原则：
    - 所有字段均为 nullable=True 或带有 server_default
    - 不影响现有表结构
    """
    # 创建发货数据表
    op.create_table(
        'shipment_data',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('customer_code', sa.String(length=50), nullable=False, comment='客户代码'),
        sa.Column('product_type', sa.String(length=100), nullable=False, comment='产品类型'),
        sa.Column('shipment_date', sa.Date(), nullable=False, comment='出货日期'),
        sa.Column('shipment_qty', sa.Integer(), nullable=False, server_default='0', comment='出货数量'),
        sa.Column('work_order', sa.String(length=50), nullable=True, comment='工单号'),
        sa.Column('batch_number', sa.String(length=50), nullable=True, comment='批次号'),
        sa.Column('destination', sa.String(length=200), nullable=True, comment='目的地'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='发货数据表 - 维护过去24个月的分月出货数据，用于计算客户质量PPM指标'
    )
    
    # 创建索引
    op.create_index('ix_shipment_data_id', 'shipment_data', ['id'], unique=False)
    op.create_index('ix_shipment_data_customer_code', 'shipment_data', ['customer_code'], unique=False)
    op.create_index('ix_shipment_data_product_type', 'shipment_data', ['product_type'], unique=False)
    op.create_index('ix_shipment_data_shipment_date', 'shipment_data', ['shipment_date'], unique=False)
    
    # 创建复合索引（优化按客户、产品、日期范围查询）
    op.create_index(
        'idx_shipment_customer_product_date',
        'shipment_data',
        ['customer_code', 'product_type', 'shipment_date'],
        unique=False
    )
    
    # 创建日期范围索引（优化滚动计算）
    op.create_index(
        'idx_shipment_date_range',
        'shipment_data',
        ['shipment_date'],
        unique=False
    )
    
    print("✅ 发货数据表创建成功")


def downgrade() -> None:
    """
    回滚操作：删除发货数据表
    
    注意：此操作会删除所有发货数据，请谨慎执行
    """
    # 删除索引
    op.drop_index('idx_shipment_date_range', table_name='shipment_data')
    op.drop_index('idx_shipment_customer_product_date', table_name='shipment_data')
    op.drop_index('ix_shipment_data_shipment_date', table_name='shipment_data')
    op.drop_index('ix_shipment_data_product_type', table_name='shipment_data')
    op.drop_index('ix_shipment_data_customer_code', table_name='shipment_data')
    op.drop_index('ix_shipment_data_id', table_name='shipment_data')
    
    # 删除表
    op.drop_table('shipment_data')
    
    print("⚠️ 发货数据表已删除")
