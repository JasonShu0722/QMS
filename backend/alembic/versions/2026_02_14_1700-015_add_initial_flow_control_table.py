"""015_add_initial_flow_control_table

Revision ID: 015_add_initial_flow_control_table
Revises: 014_add_new_product_quality_models
Create Date: 2026-02-14 17:00:00.000000

添加初期流动管理预留表：
- initial_flow_controls: 初期流动管理表（预留功能接口）

功能说明：
本迁移为预留功能接口，用于未来实现新品初期流动管理。
当前阶段仅作为静态记录，不执行系统级的生产互锁控制。

预留功能包括：
1. 加严控制配置（如：首批次100%检验、关键尺寸逐件测量）
2. 退出机制自动判断（如：连续N批次合格率达标后自动解除加严）
3. 生产互锁（未来可与MES系统对接，实现自动拦截）

Requirements: 2.8.5
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '015_add_initial_flow_control_table'
down_revision = '014_add_new_product_quality_models'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    升级数据库：创建初期流动管理预留表
    遵循非破坏性原则：所有字段均为 nullable，确保数据库兼容性
    """
    
    # 创建初期流动管理表（预留）
    op.create_table(
        'initial_flow_controls',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('project_id', sa.Integer(), nullable=True, comment='项目ID（预留）'),
        sa.Column('material_code', sa.String(length=100), nullable=True, comment='物料编码（预留）'),
        sa.Column('material_name', sa.String(length=200), nullable=True, comment='物料名称（预留）'),
        sa.Column('control_type', sa.Enum('full_inspection', 'increased_sampling', 'key_dimension_check', 'process_monitoring', 'custom', name='flowcontroltype'), nullable=True, comment='加严控制类型（预留）'),
        sa.Column('control_config', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='加严控制配置（JSON格式，预留）'),
        sa.Column('exit_criteria', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='退出机制配置（JSON格式，预留）'),
        sa.Column('auto_exit_enabled', sa.Boolean(), nullable=True, server_default='false', comment='是否启用自动退出（预留）'),
        sa.Column('exit_evaluation_data', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='退出评估数据（JSON格式，预留）'),
        sa.Column('status', sa.Enum('active', 'monitoring', 'released', 'suspended', name='flowcontrolstatus'), nullable=True, server_default='active', comment='控制状态（预留）'),
        sa.Column('production_lock_enabled', sa.Boolean(), nullable=True, server_default='false', comment='是否启用生产互锁（预留）'),
        sa.Column('lock_reason', sa.Text(), nullable=True, comment='互锁原因（预留）'),
        sa.Column('start_date', sa.DateTime(), nullable=True, comment='开始日期（预留）'),
        sa.Column('planned_end_date', sa.DateTime(), nullable=True, comment='计划结束日期（预留）'),
        sa.Column('actual_end_date', sa.DateTime(), nullable=True, comment='实际结束日期（预留）'),
        sa.Column('responsible_person_id', sa.Integer(), nullable=True, comment='责任人ID（预留）'),
        sa.Column('approver_id', sa.Integer(), nullable=True, comment='审批人ID（预留）'),
        sa.Column('remarks', sa.Text(), nullable=True, comment='备注（预留）'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.Column('updated_by', sa.Integer(), nullable=True, comment='更新人ID'),
        sa.ForeignKeyConstraint(['project_id'], ['new_product_projects.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='初期流动管理表（预留功能接口） - 用于未来实现新品初期流动管理'
    )
    op.create_index('ix_initial_flow_controls_id', 'initial_flow_controls', ['id'], unique=False)
    op.create_index('ix_initial_flow_controls_project_id', 'initial_flow_controls', ['project_id'], unique=False)
    op.create_index('ix_initial_flow_controls_material_code', 'initial_flow_controls', ['material_code'], unique=False)
    op.create_index('ix_initial_flow_controls_status', 'initial_flow_controls', ['status'], unique=False)


def downgrade() -> None:
    """
    降级数据库：删除初期流动管理预留表
    注意：生产环境禁止执行此操作
    """
    op.drop_index('ix_initial_flow_controls_status', table_name='initial_flow_controls')
    op.drop_index('ix_initial_flow_controls_material_code', table_name='initial_flow_controls')
    op.drop_index('ix_initial_flow_controls_project_id', table_name='initial_flow_controls')
    op.drop_index('ix_initial_flow_controls_id', table_name='initial_flow_controls')
    op.drop_table('initial_flow_controls')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS flowcontrolstatus')
    op.execute('DROP TYPE IF EXISTS flowcontroltype')
