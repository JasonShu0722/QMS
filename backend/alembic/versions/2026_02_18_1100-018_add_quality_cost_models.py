"""018_add_quality_cost_models

Revision ID: 018_add_quality_cost_models
Revises: 017_add_instrument_management_models
Create Date: 2026-02-18 11:00:00.000000

添加质量成本管理模块数据表（预留功能）：
- quality_costs: 质量成本记录表
- cost_analysis: 成本分析结果表

功能说明：
本迁移为质量成本管理功能预留数据表结构。当前阶段不实现业务逻辑，
仅创建表结构以支持后续功能扩展。所有字段均设置为 nullable，
确保预览环境新增此表时不影响正式环境的运行。

预留功能包括：
1. 质量成本数据归集（内部损失、外部损失、鉴定成本、预防成本）
2. 成本分析与趋势统计
3. 按供应商/产品/时间维度的成本分析
4. COQ（Cost of Quality）决策看板

Requirements: 2.11（预留功能）
Task: 16.1 创建质量成本数据模型（预留表结构）
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '018_add_quality_cost_models'
down_revision = '017_add_instrument_management_models'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    升级数据库：创建质量成本管理模块相关表（预留功能）
    
    遵循非破坏性原则：
    - 所有字段均为 nullable=True
    - 确保双轨环境兼容性
    - 预览环境可安全创建表，不影响正式环境
    """
    
    # 1. 创建质量成本记录表
    op.create_table(
        'quality_costs',
        sa.Column('id', sa.Integer(), nullable=False, comment='成本记录ID'),
        sa.Column('cost_type', sa.String(length=50), nullable=True, comment='成本类型: internal_failure/external_failure/appraisal/prevention'),
        sa.Column('cost_category', sa.String(length=100), nullable=True, comment='成本细分类别（如：报废、返工、索赔等）'),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=True, comment='成本金额'),
        sa.Column('currency', sa.String(length=10), nullable=True, comment='货币单位（默认人民币）'),
        sa.Column('related_object_type', sa.String(length=50), nullable=True, comment='关联业务类型: scar/customer_complaint/scrap/rework等'),
        sa.Column('related_object_id', sa.Integer(), nullable=True, comment='关联业务对象ID'),
        sa.Column('cost_date', sa.Date(), nullable=True, comment='成本发生日期'),
        sa.Column('fiscal_year', sa.Integer(), nullable=True, comment='财年'),
        sa.Column('fiscal_month', sa.Integer(), nullable=True, comment='财月'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='质量成本记录表（预留功能）'
    )
    
    # 创建索引
    op.create_index('ix_quality_costs_id', 'quality_costs', ['id'], unique=False)
    op.create_index('ix_quality_costs_cost_type', 'quality_costs', ['cost_type'], unique=False)
    op.create_index('ix_quality_costs_related_object_type', 'quality_costs', ['related_object_type'], unique=False)
    op.create_index('ix_quality_costs_related_object_id', 'quality_costs', ['related_object_id'], unique=False)
    op.create_index('ix_quality_costs_cost_date', 'quality_costs', ['cost_date'], unique=False)
    op.create_index('ix_quality_costs_fiscal_year', 'quality_costs', ['fiscal_year'], unique=False)
    op.create_index('ix_quality_costs_fiscal_month', 'quality_costs', ['fiscal_month'], unique=False)
    
    # 2. 创建成本分析结果表
    op.create_table(
        'cost_analysis',
        sa.Column('id', sa.Integer(), nullable=False, comment='分析记录ID'),
        sa.Column('analysis_type', sa.String(length=50), nullable=True, comment='分析类型: monthly/quarterly/yearly/supplier/product'),
        sa.Column('analysis_period', sa.String(length=50), nullable=True, comment='分析周期（如：2024-01, 2024-Q1, 2024）'),
        sa.Column('total_cost', sa.Numeric(precision=15, scale=2), nullable=True, comment='总成本金额'),
        sa.Column('analysis_result', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='分析结果详情（JSON格式）'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='成本分析结果表（预留功能）'
    )
    
    # 创建索引
    op.create_index('ix_cost_analysis_id', 'cost_analysis', ['id'], unique=False)
    op.create_index('ix_cost_analysis_analysis_type', 'cost_analysis', ['analysis_type'], unique=False)
    op.create_index('ix_cost_analysis_analysis_period', 'cost_analysis', ['analysis_period'], unique=False)


def downgrade() -> None:
    """
    降级数据库：不执行任何操作
    
    遵循非破坏性原则：
    - 预留功能的表结构不执行降级操作
    - 避免影响双轨环境的稳定性
    - 如需清理，应在所有环境停止使用后手动执行
    
    注意：如果确实需要删除这些表，请在确保所有环境（Preview和Stable）
    都不再使用这些表后，手动执行 SQL 删除操作。
    """
    # 不执行任何降级操作，保持表结构
    pass
