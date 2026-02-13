"""Add supplier meetings table

Revision ID: 007
Revises: 2026_02_13_1000-003
Create Date: 2026-02-13 15:00:00.000000

供应商会议与改进监控表
基于绩效等级的强制干预机制
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '2026_02_13_1000-003'
branch_labels = None
depends_on = None


def upgrade():
    """
    创建供应商会议表
    
    核心功能：
    1. C/D级供应商自动立项会议任务
    2. 参会人员要求通知（C级副总、D级总经理）
    3. 会议记录管理
    4. 资料上传和考勤录入
    5. 违规处罚逻辑（未参会自动扣分）
    """
    # 创建供应商会议表
    op.create_table(
        'supplier_meetings',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键'),
        sa.Column('supplier_id', sa.Integer(), nullable=False, comment='供应商ID'),
        sa.Column('performance_id', sa.Integer(), nullable=False, comment='关联的绩效评价ID'),
        sa.Column('meeting_number', sa.String(length=50), nullable=False, comment='会议编号'),
        sa.Column('meeting_date', sa.Date(), nullable=True, comment='会议日期'),
        sa.Column('performance_grade', sa.String(length=10), nullable=False, comment='触发会议的绩效等级（C或D）'),
        sa.Column('required_attendee_level', sa.String(length=50), nullable=False, comment='要求参会人员级别（C级:副总级，D级:总经理）'),
        
        # 资料上传
        sa.Column('improvement_report_path', sa.String(length=500), nullable=True, comment='物料品质问题改善报告路径'),
        sa.Column('report_uploaded_at', sa.DateTime(), nullable=True, comment='报告上传时间'),
        sa.Column('report_uploaded_by', sa.Integer(), nullable=True, comment='报告上传人ID（供应商用户）'),
        
        # 考勤与纪要
        sa.Column('actual_attendee_level', sa.String(length=50), nullable=True, comment='实际参会最高级别人员'),
        sa.Column('attendee_name', sa.String(length=100), nullable=True, comment='参会人员姓名'),
        sa.Column('attendee_position', sa.String(length=100), nullable=True, comment='参会人员职位'),
        sa.Column('meeting_minutes', sa.Text(), nullable=True, comment='会议纪要'),
        
        # 违规标记
        sa.Column('supplier_attended', sa.Boolean(), nullable=False, server_default='true', comment='供应商是否参会'),
        sa.Column('report_submitted', sa.Boolean(), nullable=False, server_default='false', comment='是否提交改善报告'),
        sa.Column('penalty_applied', sa.Boolean(), nullable=False, server_default='false', comment='是否已执行违规处罚（下月配合度扣分）'),
        sa.Column('penalty_reason', sa.Text(), nullable=True, comment='处罚原因'),
        
        # 状态管理
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending', comment='状态：pending-待召开，completed-已完成，cancelled-已取消'),
        
        # SQE记录人
        sa.Column('recorded_by', sa.Integer(), nullable=True, comment='记录人ID（SQE）'),
        sa.Column('recorded_at', sa.DateTime(), nullable=True, comment='记录时间'),
        
        # 审计字段
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        
        # 主键
        sa.PrimaryKeyConstraint('id'),
        
        # 外键约束
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], name='fk_supplier_meetings_supplier_id'),
        sa.ForeignKeyConstraint(['performance_id'], ['supplier_performances.id'], name='fk_supplier_meetings_performance_id'),
        sa.ForeignKeyConstraint(['report_uploaded_by'], ['users.id'], name='fk_supplier_meetings_report_uploaded_by'),
        sa.ForeignKeyConstraint(['recorded_by'], ['users.id'], name='fk_supplier_meetings_recorded_by'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_supplier_meetings_created_by'),
        
        # 唯一约束
        sa.UniqueConstraint('meeting_number', name='uq_supplier_meetings_meeting_number'),
        
        comment='供应商会议记录表'
    )
    
    # 创建索引
    op.create_index('ix_supplier_meetings_id', 'supplier_meetings', ['id'])
    op.create_index('ix_supplier_meetings_supplier_id', 'supplier_meetings', ['supplier_id'])
    op.create_index('ix_supplier_meetings_performance_id', 'supplier_meetings', ['performance_id'])
    op.create_index('ix_supplier_meetings_meeting_number', 'supplier_meetings', ['meeting_number'])
    op.create_index('ix_supplier_meetings_status', 'supplier_meetings', ['status'])


def downgrade():
    """回滚操作"""
    # 删除索引
    op.drop_index('ix_supplier_meetings_status', table_name='supplier_meetings')
    op.drop_index('ix_supplier_meetings_meeting_number', table_name='supplier_meetings')
    op.drop_index('ix_supplier_meetings_performance_id', table_name='supplier_meetings')
    op.drop_index('ix_supplier_meetings_supplier_id', table_name='supplier_meetings')
    op.drop_index('ix_supplier_meetings_id', table_name='supplier_meetings')
    
    # 删除表
    op.drop_table('supplier_meetings')
