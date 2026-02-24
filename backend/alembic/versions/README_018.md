# Migration 018: Quality Cost Models (Reserved Feature)

## Overview
This migration creates the database tables for the Quality Cost Management module (预留功能 - Reserved Feature).

## Created Tables

### 1. quality_costs
Records quality-related cost data including internal failures, external failures, appraisal costs, and prevention costs.

**Columns:**
- `id`: Primary key
- `cost_type`: Cost type (internal_failure/external_failure/appraisal/prevention)
- `cost_category`: Cost subcategory (e.g., scrap, rework, claims)
- `amount`: Cost amount (Numeric 15,2)
- `currency`: Currency unit (default CNY)
- `related_object_type`: Related business type (scar/customer_complaint/scrap/rework)
- `related_object_id`: Related business object ID
- `cost_date`: Cost occurrence date
- `fiscal_year`: Fiscal year
- `fiscal_month`: Fiscal month
- `created_at`: Creation timestamp
- `updated_at`: Update timestamp

**Indexes:**
- `ix_quality_costs_id`
- `ix_quality_costs_cost_type`
- `ix_quality_costs_related_object_type`
- `ix_quality_costs_related_object_id`
- `ix_quality_costs_cost_date`
- `ix_quality_costs_fiscal_year`
- `ix_quality_costs_fiscal_month`

### 2. cost_analysis
Stores quality cost analysis results supporting various analysis types and periods.

**Columns:**
- `id`: Primary key
- `analysis_type`: Analysis type (monthly/quarterly/yearly/supplier/product)
- `analysis_period`: Analysis period (e.g., 2024-01, 2024-Q1, 2024)
- `total_cost`: Total cost amount (Numeric 15,2)
- `analysis_result`: Analysis result details (JSON format)
- `created_at`: Creation timestamp
- `updated_at`: Update timestamp

**Indexes:**
- `ix_cost_analysis_id`
- `ix_cost_analysis_analysis_type`
- `ix_cost_analysis_analysis_period`

## Compatibility Notes

### Dual-Track Environment Compatibility
All fields are set to `nullable=True` to ensure compatibility with the dual-track deployment architecture:
- Preview environment can safely create these tables
- Stable environment continues to run without issues
- No breaking changes to existing code

### Non-Destructive Migration Principles
This migration follows the non-destructive principles:
- ✅ Only adds new tables
- ✅ All columns are nullable
- ✅ No modifications to existing tables
- ✅ No column deletions or renames
- ✅ Safe for dual-track deployment

## How to Apply

### Using Docker Compose
```bash
# Run migration in the backend container
docker-compose exec backend-stable alembic upgrade head

# Or for preview environment
docker-compose exec backend-preview alembic upgrade head
```

### Using Local Python Environment
```bash
cd backend
alembic upgrade head
```

## Verification

After applying the migration, verify the tables were created:

```sql
-- Check if tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('quality_costs', 'cost_analysis');

-- Check table structure
\d quality_costs
\d cost_analysis
```

## Related Files
- Model: `backend/app/models/quality_cost.py`
- Migration: `backend/alembic/versions/2026_02_18_1100-018_add_quality_cost_models.py`
- Requirements: Section 2.11 (Reserved Feature)
- Task: 16.1 创建质量成本数据模型（预留表结构）

## Future Implementation
This is a reserved feature. Business logic implementation will be added in a future phase when the Quality Cost Management module is activated.
