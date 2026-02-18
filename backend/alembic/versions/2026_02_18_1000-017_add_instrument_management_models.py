"""017_add_instrument_management_models

Revision ID: 017_add_instrument_management_models
Revises: 016_add_audit_management_models
Create Date: 2026-02-18 10:00:00.000000

添加仪器量具管理模块数据表（预留功能）：
- instruments: 仪器量具基本信息表
- msa_records: MSA分析记录表

功能说明：
本迁移为仪器量具管理功能预留数据表结构。当前阶段不实现业务逻辑，
仅创建表结构以支持后续功能扩展。所有字段均设置为 nullable，
确保预览环境新增此表时不影响正式环境的运行。

预留功能包括：
1. 仪器量具电子台账管理
2. 校准周期管理与到期预警
3. MSA（测量系统分析）记录管理
4. 仪器状态互锁（过期自动冻结）

Requirements: 2.10（预留功能）
Task: 15.1 创建仪器量具数据模型（预留表结构）
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '017_add_instrument_management_models'
down_revision = '016_add_audit_management_models'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    升级数据库：创建仪器量具管理模块相关表（预留功能）
    
    遵循非破坏性原则：
    - 所有字段均为 nullable=True
    - 确保双轨环境兼容性
    - 预览环境可安全创建表，不影响正式环境
    """
    
    # 1. 创建仪器量具基本信息表
    op.create_table(
        'instruments',
        sa.Column('id', sa.Integer(), nullable=False, comment='仪器ID'),
        sa.Column('instrument_code', sa.String(length=100), nullable=True, comment='仪器编码（唯一标识）'),
        sa.Column('instrument_name', sa.String(length=255), nullable=True, comment='仪器名称'),
        sa.Column('instrument_type', sa.String(length=50), nullable=True, comment='仪器类型: measuring/testing/calibration/inspection/other'),
        sa.Column('calibration_date', sa.Date(), nullable=True, comment='最近校准日期'),
        sa.Column('next_calibration_date', sa.Date(), nullable=True, comment='下次校准日期'),
        sa.Column('calibration_cert_path', sa.String(length=500), nullable=True, comment='校准证书文件路径'),
        sa.Column('status', sa.String(length=20), nullable=True, comment='仪器状态: active/expired/frozen/retired'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人用户ID'),
        sa.Column('updated_by', sa.Integer(), nullable=True, comment='更新人用户ID'),
        sa.PrimaryKeyConstraint('id'),
        comment='仪器量具基本信息表（预留功能）'
    )
    
    # 创建索引
    op.create_index('ix_instruments_id', 'instruments', ['id'], unique=False)
    op.create_index('ix_instruments_instrument_code', 'instruments', ['instrument_code'], unique=True)
    op.create_index('ix_instruments_instrument_type', 'instruments', ['instrument_type'], unique=False)
    op.create_index('ix_instruments_next_calibration_date', 'instruments', ['next_calibration_date'], unique=False)
    op.create_index('ix_instruments_status', 'instruments', ['status'], unique=False)
    
    # 2. 创建MSA分析记录表
    op.create_table(
        'msa_records',
        sa.Column('id', sa.Integer(), nullable=False, comment='MSA记录ID'),
        sa.Column('instrument_id', sa.Integer(), nullable=True, comment='关联的仪器ID'),
        sa.Column('msa_type', sa.String(length=50), nullable=True, comment='MSA分析类型: grr/bias/linearity/stability/other'),
        sa.Column('msa_date', sa.Date(), nullable=True, comment='MSA分析日期'),
        sa.Column('msa_result', sa.String(length=20), nullable=True, comment='MSA分析结果: pass/fail/conditional'),
        sa.Column('msa_report_path', sa.String(length=500), nullable=True, comment='MSA分析报告文件路径'),
        sa.Column('grr_percentage', sa.String(length=20), nullable=True, comment='GRR百分比（如适用）'),
        sa.Column('remarks', sa.Text(), nullable=True, comment='备注说明'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人用户ID'),
        sa.Column('updated_by', sa.Integer(), nullable=True, comment='更新人用户ID'),
        sa.ForeignKeyConstraint(['instrument_id'], ['instruments.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='MSA分析记录表（预留功能）'
    )
    
    # 创建索引
    op.create_index('ix_msa_records_id', 'msa_records', ['id'], unique=False)
    op.create_index('ix_msa_records_instrument_id', 'msa_records', ['instrument_id'], unique=False)
    op.create_index('ix_msa_records_msa_type', 'msa_records', ['msa_type'], unique=False)
    op.create_index('ix_msa_records_msa_date', 'msa_records', ['msa_date'], unique=False)
    op.create_index('ix_msa_records_msa_result', 'msa_records', ['msa_result'], unique=False)


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
