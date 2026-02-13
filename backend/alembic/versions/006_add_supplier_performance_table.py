"""Add supplier performance table

Revision ID: 006
Revises: 005
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    """
    创建供应商绩效评价表
    
    遵循非破坏性迁移原则：
    - 所有字段设置为 nullable=True 或带有 server_default
    - 确保双轨环境兼容性
    """
    # 创建供应商绩效评价表
    op.create_table(
        'supplier_performances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        
        # 扣分明细（60分制）
        sa.Column('incoming_quality_deduction', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('process_quality_deduction', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('cooperation_deduction', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('zero_km_deduction', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('total_deduction', sa.Float(), nullable=False, server_default='0.0'),
        
        # 最终得分和等级
        sa.Column('final_score', sa.Float(), nullable=False),
        sa.Column('grade', sa.String(length=10), nullable=False),
        
        # 配合度评价
        sa.Column('cooperation_level', sa.String(length=20), nullable=True),
        sa.Column('cooperation_comment', sa.Text(), nullable=True),
        
        # SQE人工校核
        sa.Column('is_reviewed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('review_comment', sa.Text(), nullable=True),
        sa.Column('manual_adjustment', sa.Float(), nullable=False, server_default='0.0'),
        
        # 审计字段
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # 主键
        sa.PrimaryKeyConstraint('id'),
        
        # 外键
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
        
        # 唯一约束：每个供应商每月只能有一条绩效记录
        sa.UniqueConstraint('supplier_id', 'year', 'month', name='uq_supplier_year_month'),
        
        comment='供应商绩效评价表'
    )
    
    # 创建索引
    op.create_index('ix_supplier_performances_supplier_id', 'supplier_performances', ['supplier_id'])
    op.create_index('ix_supplier_performances_year', 'supplier_performances', ['year'])
    op.create_index('ix_supplier_performances_month', 'supplier_performances', ['month'])
    op.create_index('ix_supplier_performances_grade', 'supplier_performances', ['grade'])
    op.create_index('ix_supplier_performances_year_month', 'supplier_performances', ['year', 'month'])


def downgrade():
    """
    回滚操作
    
    注意：在生产环境中，downgrade 操作需要谨慎执行
    """
    op.drop_index('ix_supplier_performances_year_month', table_name='supplier_performances')
    op.drop_index('ix_supplier_performances_grade', table_name='supplier_performances')
    op.drop_index('ix_supplier_performances_month', table_name='supplier_performances')
    op.drop_index('ix_supplier_performances_year', table_name='supplier_performances')
    op.drop_index('ix_supplier_performances_supplier_id', table_name='supplier_performances')
    op.drop_table('supplier_performances')
