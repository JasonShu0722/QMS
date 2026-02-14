"""012_add_customer_quality_models

Revision ID: 012_add_customer_quality_models
Revises: 008_add_process_quality_models
Create Date: 2026-02-14 14:00:00.000000

添加客户质量管理模块数据模型：
- customer_complaints: 客诉单表
- eight_d_customer: 客诉8D报告表
- customer_claims: 客户索赔表
- supplier_claims: 供应商索赔表
- lesson_learned: 经验教训表
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '012_add_customer_quality_models'
down_revision = '008_add_process_quality_models'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    升级数据库：创建客户质量管理相关表
    遵循非破坏性原则：所有新增字段均为 nullable 或带有默认值
    """
    
    # 1. 创建客诉单表
    op.create_table(
        'customer_complaints',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('complaint_number', sa.String(length=50), nullable=False, comment='客诉单号'),
        sa.Column('complaint_type', sa.Enum('0km', 'after_sales', name='complainttype'), nullable=False, comment='客诉类型：0km/售后'),
        sa.Column('customer_code', sa.String(length=50), nullable=False, comment='客户代码'),
        sa.Column('product_type', sa.String(length=100), nullable=False, comment='产品类型'),
        sa.Column('defect_description', sa.Text(), nullable=False, comment='缺陷描述'),
        sa.Column('severity_level', sa.Enum('critical', 'major', 'minor', 'tbd', name='severitylevel'), nullable=False, server_default='tbd', comment='严重度等级'),
        sa.Column('vin_code', sa.String(length=50), nullable=True, comment='VIN码（车架号）'),
        sa.Column('mileage', sa.Integer(), nullable=True, comment='失效里程（公里）'),
        sa.Column('purchase_date', sa.Date(), nullable=True, comment='购车日期'),
        sa.Column('status', sa.Enum('pending', 'in_analysis', 'in_response', 'in_review', 'closed', 'rejected', name='complaintstatus'), nullable=False, server_default='pending', comment='客诉状态'),
        sa.Column('cqe_id', sa.Integer(), nullable=True, comment='负责CQE的用户ID'),
        sa.Column('responsible_dept', sa.String(length=100), nullable=True, comment='责任部门'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.ForeignKeyConstraint(['cqe_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='客诉单表 - 记录0KM客诉和售后客诉'
    )
    op.create_index('ix_customer_complaints_complaint_number', 'customer_complaints', ['complaint_number'], unique=True)
    op.create_index('ix_customer_complaints_customer_code', 'customer_complaints', ['customer_code'], unique=False)
    op.create_index('ix_customer_complaints_id', 'customer_complaints', ['id'], unique=False)
    
    # 2. 创建客诉8D报告表
    op.create_table(
        'eight_d_customer',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('complaint_id', sa.Integer(), nullable=False, comment='关联的客诉单ID'),
        sa.Column('d0_d3_cqe', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='D0-D3阶段数据（CQE负责）'),
        sa.Column('d4_d7_responsible', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='D4-D7阶段数据（责任板块负责）'),
        sa.Column('d8_horizontal', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='D8阶段数据（水平展开与经验教训）'),
        sa.Column('status', sa.Enum('draft', 'd0_d3_completed', 'd4_d7_in_progress', 'd4_d7_completed', 'd8_in_progress', 'in_review', 'approved', 'rejected', 'closed', name='eightdstatus'), nullable=False, server_default='draft', comment='8D报告状态'),
        sa.Column('approval_level', sa.Enum('section_manager', 'department_head', 'none', name='approvallevel'), nullable=False, server_default='none', comment='审批级别'),
        sa.Column('submitted_at', sa.DateTime(), nullable=True, comment='提交时间'),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True, comment='审核时间'),
        sa.Column('reviewed_by', sa.Integer(), nullable=True, comment='审核人ID'),
        sa.Column('review_comments', sa.Text(), nullable=True, comment='审核意见'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.ForeignKeyConstraint(['complaint_id'], ['customer_complaints.id'], ),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('complaint_id'),
        comment='客诉8D报告表 - 记录客诉问题的8D分析过程'
    )
    op.create_index('ix_eight_d_customer_id', 'eight_d_customer', ['id'], unique=False)
    
    # 3. 创建客户索赔表
    op.create_table(
        'customer_claims',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('complaint_id', sa.Integer(), nullable=False, comment='关联的客诉单ID'),
        sa.Column('claim_amount', sa.Numeric(precision=15, scale=2), nullable=False, comment='索赔金额'),
        sa.Column('claim_currency', sa.String(length=10), nullable=False, server_default='CNY', comment='币种（CNY/USD/EUR等）'),
        sa.Column('claim_date', sa.Date(), nullable=False, comment='索赔日期'),
        sa.Column('customer_name', sa.String(length=200), nullable=False, comment='客户名称'),
        sa.Column('claim_description', sa.String(length=500), nullable=True, comment='索赔说明'),
        sa.Column('claim_reference', sa.String(length=100), nullable=True, comment='客户索赔单号'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.ForeignKeyConstraint(['complaint_id'], ['customer_complaints.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='客户索赔表 - 记录客户对公司的索赔信息'
    )
    op.create_index('ix_customer_claims_complaint_id', 'customer_claims', ['complaint_id'], unique=False)
    op.create_index('ix_customer_claims_id', 'customer_claims', ['id'], unique=False)
    
    # 4. 创建供应商索赔表
    op.create_table(
        'supplier_claims',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('complaint_id', sa.Integer(), nullable=True, comment='关联的客诉单ID（可选）'),
        sa.Column('supplier_id', sa.Integer(), nullable=False, comment='供应商ID'),
        sa.Column('claim_amount', sa.Numeric(precision=15, scale=2), nullable=False, comment='索赔金额'),
        sa.Column('claim_currency', sa.String(length=10), nullable=False, server_default='CNY', comment='币种（CNY/USD/EUR等）'),
        sa.Column('claim_date', sa.Date(), nullable=False, comment='索赔日期'),
        sa.Column('claim_description', sa.String(length=500), nullable=True, comment='索赔说明'),
        sa.Column('material_code', sa.String(length=50), nullable=True, comment='涉及物料编码'),
        sa.Column('defect_qty', sa.Integer(), nullable=True, comment='不良数量'),
        sa.Column('status', sa.Enum('draft', 'submitted', 'under_negotiation', 'accepted', 'rejected', 'partially_accepted', 'paid', 'closed', name='supplierclaimstatus'), nullable=False, server_default='draft', comment='索赔状态'),
        sa.Column('negotiation_notes', sa.String(length=1000), nullable=True, comment='协商记录'),
        sa.Column('final_amount', sa.Numeric(precision=15, scale=2), nullable=True, comment='最终索赔金额（协商后）'),
        sa.Column('payment_date', sa.Date(), nullable=True, comment='实际支付日期'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.ForeignKeyConstraint(['complaint_id'], ['customer_complaints.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='供应商索赔表 - 记录公司对供应商的索赔信息'
    )
    op.create_index('ix_supplier_claims_complaint_id', 'supplier_claims', ['complaint_id'], unique=False)
    op.create_index('ix_supplier_claims_id', 'supplier_claims', ['id'], unique=False)
    op.create_index('ix_supplier_claims_supplier_id', 'supplier_claims', ['supplier_id'], unique=False)
    
    # 5. 创建经验教训表
    op.create_table(
        'lesson_learned',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('source_type', sa.Enum('customer_complaint', 'supplier_8d', 'process_issue', 'manual', name='sourcetype'), nullable=False, comment='来源类型'),
        sa.Column('source_id', sa.Integer(), nullable=True, comment='来源记录ID（如客诉单ID、8D报告ID）'),
        sa.Column('lesson_title', sa.String(length=200), nullable=False, comment='经验教训标题'),
        sa.Column('lesson_content', sa.Text(), nullable=False, comment='经验教训详细内容'),
        sa.Column('root_cause', sa.Text(), nullable=False, comment='根本原因'),
        sa.Column('preventive_action', sa.Text(), nullable=False, comment='预防措施'),
        sa.Column('applicable_scenarios', sa.String(length=500), nullable=True, comment='适用场景标签（逗号分隔）'),
        sa.Column('product_types', sa.String(length=200), nullable=True, comment='适用产品类型（逗号分隔）'),
        sa.Column('process_types', sa.String(length=200), nullable=True, comment='适用工序类型（逗号分隔）'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='是否启用（用于经验教训库管理）'),
        sa.Column('approved_by', sa.Integer(), nullable=True, comment='批准人ID'),
        sa.Column('approved_at', sa.DateTime(), nullable=True, comment='批准时间'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='经验教训表 - 记录从质量问题中沉淀的经验教训'
    )
    op.create_index('ix_lesson_learned_id', 'lesson_learned', ['id'], unique=False)


def downgrade() -> None:
    """
    降级数据库：删除客户质量管理相关表
    注意：生产环境禁止执行此操作
    """
    op.drop_index('ix_lesson_learned_id', table_name='lesson_learned')
    op.drop_table('lesson_learned')
    
    op.drop_index('ix_supplier_claims_supplier_id', table_name='supplier_claims')
    op.drop_index('ix_supplier_claims_id', table_name='supplier_claims')
    op.drop_index('ix_supplier_claims_complaint_id', table_name='supplier_claims')
    op.drop_table('supplier_claims')
    
    op.drop_index('ix_customer_claims_id', table_name='customer_claims')
    op.drop_index('ix_customer_claims_complaint_id', table_name='customer_claims')
    op.drop_table('customer_claims')
    
    op.drop_index('ix_eight_d_customer_id', table_name='eight_d_customer')
    op.drop_table('eight_d_customer')
    
    op.drop_index('ix_customer_complaints_id', table_name='customer_complaints')
    op.drop_index('ix_customer_complaints_customer_code', table_name='customer_complaints')
    op.drop_index('ix_customer_complaints_complaint_number', table_name='customer_complaints')
    op.drop_table('customer_complaints')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS sourcetype')
    op.execute('DROP TYPE IF EXISTS supplierclaimstatus')
    op.execute('DROP TYPE IF EXISTS approvallevel')
    op.execute('DROP TYPE IF EXISTS eightdstatus')
    op.execute('DROP TYPE IF EXISTS complaintstatus')
    op.execute('DROP TYPE IF EXISTS severitylevel')
    op.execute('DROP TYPE IF EXISTS complainttype')
