"""
API tests for shared problem-management metadata and first-batch issue summaries.
"""
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditExecution, AuditNC, AuditPlan, AuditTemplate
from app.models.new_product_project import NewProductProject, ProjectStage, ProjectStatus
from app.models.process_defect import ProcessDefect, ResponsibilityCategory
from app.models.process_issue import ProcessIssue, ProcessIssueStatus
from app.models.scar import SCAR, SCARSeverity, SCARStatus
from app.models.supplier import Supplier, SupplierStatus
from app.models.trial_issue import IssueStatus, IssueType, TrialIssue
from app.models.trial_production import TrialProduction, TrialStatus
from app.models.user import User, UserStatus, UserType
from app.core.auth_strategy import LocalAuthStrategy
from app.schemas.scar import EightDSubmit
from app.services.scar_service import EightDService


async def _seed_audit_nc(
    db_session: AsyncSession,
    *,
    user: User,
    audit_type: str,
    name_suffix: str,
    verification_status: str = "open",
) -> AuditNC:
    now = datetime.utcnow()

    plan = AuditPlan(
        audit_type=audit_type,
        audit_name=f"Audit Plan {name_suffix}",
        planned_date=now + timedelta(days=1),
        auditor_id=user.id,
        auditee_dept="Quality",
        status="planned",
        created_at=now,
        updated_at=now,
        created_by=user.id,
    )
    db_session.add(plan)
    await db_session.flush()

    template = AuditTemplate(
        template_name=f"Template {name_suffix}",
        audit_type=audit_type,
        checklist_items={"items": []},
        scoring_rules={"rules": []},
        description="test template",
        is_builtin=False,
        is_active=True,
        created_at=now,
        updated_at=now,
        created_by=user.id,
    )
    db_session.add(template)
    await db_session.flush()

    execution = AuditExecution(
        audit_plan_id=plan.id,
        template_id=template.id,
        audit_date=now,
        auditor_id=user.id,
        audit_team={"members": []},
        checklist_results={"items": []},
        final_score=None,
        grade=None,
        audit_report_path=None,
        summary=None,
        status="nc_open",
        created_at=now,
        updated_at=now,
        created_by=user.id,
    )
    db_session.add(execution)
    await db_session.flush()

    nc = AuditNC(
        audit_id=execution.id,
        nc_item=f"Clause {name_suffix}",
        nc_description=f"Problem {name_suffix}",
        evidence_photo_path=None,
        responsible_dept="Quality",
        assigned_to=user.id,
        root_cause=None,
        corrective_action=None,
        corrective_evidence=None,
        verification_status=verification_status,
        verified_by=None,
        verified_at=None,
        verification_comment=None,
        deadline=now + timedelta(days=3),
        closed_at=None,
        created_at=now,
        updated_at=now,
        created_by=user.id,
    )
    db_session.add(nc)
    await db_session.commit()
    await db_session.refresh(nc)
    return nc


async def _seed_process_issue(
    db_session: AsyncSession,
    *,
    user: User,
    name_suffix: str,
    process_id: str,
    line_id: str,
    issue_description: str,
    issue_status: ProcessIssueStatus = ProcessIssueStatus.OPEN,
) -> ProcessIssue:
    now = datetime.utcnow()

    defect = ProcessDefect(
        defect_date=now.date(),
        work_order=f"WO-{name_suffix}",
        process_id=process_id,
        line_id=line_id,
        defect_type="solder defect" if "smt" in process_id.lower() else "assembly test abnormal",
        defect_qty=3,
        responsibility_category=ResponsibilityCategory.PROCESS_DEFECT,
        operator_id=None,
        recorded_by=user.id,
        material_code=None,
        supplier_id=None,
        remarks=None,
        created_at=now,
        updated_at=now,
    )
    db_session.add(defect)
    await db_session.flush()

    issue = ProcessIssue(
        issue_number=f"PQI-20260424-{name_suffix[-4:]}",
        issue_description=issue_description,
        responsibility_category=ResponsibilityCategory.PROCESS_DEFECT,
        assigned_to=user.id,
        root_cause=None,
        containment_action=None,
        corrective_action=None,
        verification_period=7 if issue_status == ProcessIssueStatus.IN_VERIFICATION else None,
        verification_start_date=now.date() if issue_status == ProcessIssueStatus.IN_VERIFICATION else None,
        verification_end_date=now.date() + timedelta(days=7) if issue_status == ProcessIssueStatus.IN_VERIFICATION else None,
        status=issue_status,
        related_defect_ids=str(defect.id),
        evidence_files=None,
        created_by=user.id,
        verified_by=None,
        closed_by=None,
        closed_at=None,
        created_at=now,
        updated_at=now,
    )
    db_session.add(issue)
    await db_session.commit()
    await db_session.refresh(issue)
    return issue


async def _seed_trial_issue(
    db_session: AsyncSession,
    *,
    user: User,
    name_suffix: str,
    issue_description: str,
    issue_status: IssueStatus = IssueStatus.OPEN,
    issue_type: IssueType = IssueType.PROCESS,
    assigned_dept: str = "试产工艺部",
    is_escalated_to_8d: bool = False,
) -> TrialIssue:
    now = datetime.utcnow()

    project = NewProductProject(
        project_code=f"NP-{name_suffix}",
        project_name=f"Trial Project {name_suffix}",
        product_type="MODULE-NP",
        project_manager="PM",
        project_manager_id=user.id,
        current_stage=ProjectStage.TRIAL_PRODUCTION,
        status=ProjectStatus.ACTIVE,
        created_at=now,
        updated_at=now,
        created_by=user.id,
        updated_by=user.id,
    )
    db_session.add(project)
    await db_session.flush()

    trial = TrialProduction(
        project_id=project.id,
        work_order=f"WO-TRIAL-{name_suffix}",
        trial_batch=f"BATCH-{name_suffix}",
        trial_date=now,
        status=TrialStatus.IN_PROGRESS,
        created_at=now,
        updated_at=now,
        created_by=user.id,
        updated_by=user.id,
    )
    db_session.add(trial)
    await db_session.flush()

    issue = TrialIssue(
        trial_id=trial.id,
        issue_number=f"TI-2026-{name_suffix[-4:]}",
        issue_description=issue_description,
        issue_type=issue_type,
        assigned_to=user.id,
        assigned_dept=assigned_dept,
        root_cause=None,
        solution="Escalated to 8D" if is_escalated_to_8d else None,
        solution_file_path=None,
        verification_method=None,
        verification_result=None,
        verified_by=None,
        verified_at=None,
        status=issue_status,
        is_escalated_to_8d=is_escalated_to_8d,
        eight_d_id=88 if is_escalated_to_8d else None,
        escalated_at=now if is_escalated_to_8d else None,
        escalation_reason="Complex issue, escalate to 8D" if is_escalated_to_8d else None,
        is_legacy_issue=False,
        legacy_approval_status=None,
        legacy_approval_by=None,
        legacy_approval_at=None,
        risk_acknowledgement_path=None,
        deadline=now + timedelta(days=5),
        resolved_at=now if issue_status == IssueStatus.RESOLVED else None,
        closed_at=now if issue_status == IssueStatus.CLOSED else None,
        created_at=now,
        updated_at=now,
        created_by=user.id,
    )
    db_session.add(issue)
    await db_session.commit()
    await db_session.refresh(issue)
    return issue


async def _seed_scar(
    db_session: AsyncSession,
    *,
    user: User,
    name_suffix: str,
    material_code: str,
    defect_description: str,
    scar_status: SCARStatus = SCARStatus.OPEN,
) -> SCAR:
    now = datetime.utcnow()

    supplier = Supplier(
        name=f"Supplier {name_suffix}",
        code=f"SUP-{name_suffix}",
        contact_person="SQE",
        contact_email=f"supplier-{name_suffix}@example.com",
        contact_phone="13800000000",
        status=SupplierStatus.ACTIVE,
        created_at=now,
        updated_at=now,
        created_by=user.id,
        updated_by=user.id,
    )
    db_session.add(supplier)
    await db_session.flush()

    scar = SCAR(
        scar_number=f"SCAR-20260424-{name_suffix[-4:]}",
        supplier_id=supplier.id,
        material_code=material_code,
        defect_description=defect_description,
        defect_qty=12,
        severity=SCARSeverity.HIGH,
        status=scar_status,
        current_handler_id=user.id,
        deadline=now + timedelta(days=4),
        created_at=now,
        updated_at=now,
        created_by=user.id,
        updated_by=user.id,
    )
    db_session.add(scar)
    await db_session.commit()
    await db_session.refresh(scar)
    return scar


async def _seed_internal_user(
    db_session: AsyncSession,
    *,
    suffix: str,
) -> User:
    now = datetime.utcnow()
    auth_strategy = LocalAuthStrategy()

    user = User(
        username=f"problem-user-{suffix}",
        password_hash=auth_strategy.hash_password("Test@1234"),
        full_name=f"Problem User {suffix}",
        email=f"problem-user-{suffix}@example.com",
        phone="13800138001",
        user_type=UserType.INTERNAL,
        status=UserStatus.ACTIVE,
        department="质量部",
        position="质量工程师",
        password_changed_at=now,
        created_at=now,
        updated_at=now,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_get_problem_management_catalog_requires_auth(async_client: AsyncClient):
    response = await async_client.get("/api/v1/problem-management/catalog")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_problem_management_catalog_returns_confirmed_metadata(
    async_client: AsyncClient,
    test_user_token: str,
):
    headers = {"Authorization": f"Bearer {test_user_token}"}

    response = await async_client.get(
        "/api/v1/problem-management/catalog",
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert data["response_modes"] == ["brief", "eight_d"]
    assert data["handling_levels"] == ["simple", "complex", "major"]
    assert data["numbering_rule"]["issue_prefix"] == "ZXQ"
    assert data["numbering_rule"]["report_prefix"] == "ZX8D"
    assert data["numbering_rule"]["issue_pattern"] == "ZXQ-<分类子类>-<YYMM>-<SEQ3>"
    assert any(item["key"] == "CQ1" and item["label"] == "售后" for item in data["categories"])
    assert any(item["key"] == "IQ0" and item["label"] == "结构料" for item in data["categories"])
    assert any(item["key"] == "AQ3" and item["label"] == "客户审核问题" for item in data["categories"])


@pytest.mark.asyncio
async def test_get_problem_management_issue_summaries_returns_all_first_batch_items(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_user: User,
    test_user_token: str,
):
    headers = {"Authorization": f"Bearer {test_user_token}"}

    create_response = await async_client.post(
        "/api/v1/customer-complaints",
        headers=headers,
        json={
            "complaint_type": "0km",
            "customer_code": "CUST200",
            "product_type": "MODULE-Z",
            "defect_description": "first-batch summary should aggregate customer complaints too",
            "requires_physical_analysis": False,
        },
    )
    assert create_response.status_code == 201

    await _seed_audit_nc(
        db_session,
        user=test_user,
        audit_type="customer_audit",
        name_suffix="summary",
        verification_status="assigned",
    )
    await _seed_process_issue(
        db_session,
        user=test_user,
        name_suffix="1001",
        process_id="SMT-01",
        line_id="LINE-PCBA",
        issue_description="SMT solder defect should appear in the unified problem center",
        issue_status=ProcessIssueStatus.IN_ANALYSIS,
    )
    await _seed_scar(
        db_session,
        user=test_user,
        name_suffix="3001",
        material_code="HOUSING-001",
        defect_description="housing crack found on structure part",
        scar_status=SCARStatus.OPEN,
    )
    await _seed_trial_issue(
        db_session,
        user=test_user,
        name_suffix="2001",
        issue_description="trial debug issue should appear in the unified problem center",
        issue_status=IssueStatus.IN_PROGRESS,
    )

    response = await async_client.get(
        "/api/v1/problem-management/issues",
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 5
    assert data["module_counts"] == {
        "customer_quality": 1,
        "audit_management": 1,
        "process_quality": 1,
        "incoming_quality": 1,
        "new_product_quality": 1,
    }
    module_keys = {item["module_key"] for item in data["items"]}
    assert module_keys == {
        "customer_quality",
        "audit_management",
        "process_quality",
        "incoming_quality",
        "new_product_quality",
    }

    customer_item = next(item for item in data["items"] if item["source_type"] == "customer_complaint")
    assert customer_item["problem_category_key"] == "CQ0"
    assert customer_item["problem_category_label"] == "0km"
    assert customer_item["reference_no"].startswith("CC-")
    assert customer_item["unified_status"] == "open"
    assert customer_item["response_mode"] == "brief"
    assert customer_item["requires_physical_analysis"] is False
    assert customer_item["assigned_to"] == test_user.id
    assert customer_item["action_owner_id"] == test_user.id

    audit_item = next(item for item in data["items"] if item["source_type"] == "audit_nc")
    assert audit_item["problem_category_key"] == "AQ3"
    assert audit_item["unified_status"] == "assigned"
    assert audit_item["reference_no"].startswith("NC-")
    assert audit_item["action_owner_id"] == test_user.id

    process_item = next(item for item in data["items"] if item["source_type"] == "process_issue")
    assert process_item["problem_category_key"] == "PQ0"
    assert process_item["problem_category_label"] == "PCBA段"
    assert process_item["reference_no"].startswith("PQI-")
    assert process_item["unified_status"] == "responding"
    assert process_item["response_mode"] == "brief"
    assert process_item["action_owner_id"] == test_user.id
    assert process_item["verified_by"] is None

    scar_item = next(item for item in data["items"] if item["source_type"] == "scar")
    assert scar_item["problem_category_key"] == "IQ0"
    assert scar_item["problem_category_label"] == "结构料"
    assert scar_item["reference_no"].startswith("SCAR-")
    assert scar_item["unified_status"] == "open"
    assert scar_item["response_mode"] == "eight_d"
    assert scar_item["action_owner_id"] == test_user.id

    trial_item = next(item for item in data["items"] if item["source_type"] == "trial_issue")
    assert trial_item["problem_category_key"] == "DQ0"
    assert trial_item["problem_category_label"] == "厂内试产/调试问题"
    assert trial_item["reference_no"].startswith("TI-")
    assert trial_item["unified_status"] == "responding"
    assert trial_item["response_mode"] == "brief"
    assert trial_item["action_owner_id"] == test_user.id

    actionable_response = await async_client.get(
        "/api/v1/problem-management/issues",
        headers=headers,
        params={
            "only_actionable_to_me": True,
        },
    )
    assert actionable_response.status_code == 200
    actionable_data = actionable_response.json()
    assert actionable_data["total"] == 4
    assert actionable_data["module_counts"] == {
        "customer_quality": 1,
        "audit_management": 1,
        "process_quality": 1,
        "new_product_quality": 1,
    }
    assert {item["source_type"] for item in actionable_data["items"]} == {
        "customer_complaint",
        "audit_nc",
        "process_issue",
        "trial_issue",
    }


@pytest.mark.asyncio
async def test_get_problem_management_issue_summaries_filters_by_module_and_status(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_user: User,
    test_user_token: str,
):
    headers = {"Authorization": f"Bearer {test_user_token}"}

    create_response = await async_client.post(
        "/api/v1/customer-complaints",
        headers=headers,
        json={
            "complaint_type": "after_sales",
            "customer_code": "CUST201",
            "product_type": "MODULE-Y",
            "defect_description": "after-sales complaint should stay filterable in the unified issue center",
            "requires_physical_analysis": False,
            "vin_code": "LSVAA4182E2123456",
            "mileage": 12000,
            "purchase_date": "2024-01-01",
        },
    )
    assert create_response.status_code == 201

    await _seed_audit_nc(
        db_session,
        user=test_user,
        audit_type="process_audit",
        name_suffix="status-filter",
        verification_status="submitted",
    )
    await _seed_process_issue(
        db_session,
        user=test_user,
        name_suffix="1002",
        process_id="ASSY-TEST-01",
        line_id="LINE-ASSY",
        issue_description="assembly test issue should map to PQ1 while verifying",
        issue_status=ProcessIssueStatus.IN_VERIFICATION,
    )
    await _seed_scar(
        db_session,
        user=test_user,
        name_suffix="3002",
        material_code="PCB-CONN-001",
        defect_description="connector solder issue on electronic component",
        scar_status=SCARStatus.UNDER_REVIEW,
    )
    await _seed_trial_issue(
        db_session,
        user=test_user,
        name_suffix="2002",
        issue_description="trial issue escalated to 8D should remain filterable as DQ0",
        issue_status=IssueStatus.ESCALATED,
        assigned_dept="新品质量部",
        is_escalated_to_8d=True,
    )
    other_user = await _seed_internal_user(db_session, suffix="other")
    await _seed_process_issue(
        db_session,
        user=other_user,
        name_suffix="1003",
        process_id="SMT-02",
        line_id="LINE-PCBA-02",
        issue_description="another user's process issue should be excluded from my assigned view",
        issue_status=ProcessIssueStatus.IN_ANALYSIS,
    )

    response = await async_client.get(
        "/api/v1/problem-management/issues",
        headers=headers,
        params={
            "module_key": "audit_management",
            "unified_status": "pending_review",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["source_type"] == "audit_nc"
    assert data["items"][0]["problem_category_key"] == "AQ1"

    complaint_response = await async_client.get(
        "/api/v1/problem-management/issues",
        headers=headers,
        params={
            "problem_category_key": "CQ1",
        },
    )
    assert complaint_response.status_code == 200
    complaint_data = complaint_response.json()
    assert complaint_data["total"] == 1
    assert complaint_data["items"][0]["source_type"] == "customer_complaint"
    assert complaint_data["items"][0]["problem_category_key"] == "CQ1"

    process_response = await async_client.get(
        "/api/v1/problem-management/issues",
        headers=headers,
        params={
            "module_key": "process_quality",
            "problem_category_key": "PQ1",
            "unified_status": "verifying",
        },
    )
    assert process_response.status_code == 200
    process_data = process_response.json()
    assert process_data["total"] == 1
    assert process_data["items"][0]["source_type"] == "process_issue"
    assert process_data["items"][0]["problem_category_key"] == "PQ1"
    assert process_data["items"][0]["unified_status"] == "verifying"
    assert process_data["items"][0]["action_owner_id"] == test_user.id
    assert process_data["items"][0]["verified_by"] is None

    scar_response = await async_client.get(
        "/api/v1/problem-management/issues",
        headers=headers,
        params={
            "module_key": "incoming_quality",
            "problem_category_key": "IQ1",
            "unified_status": "pending_review",
        },
    )
    assert scar_response.status_code == 200
    scar_data = scar_response.json()
    assert scar_data["total"] == 1
    assert scar_data["items"][0]["source_type"] == "scar"
    assert scar_data["items"][0]["problem_category_key"] == "IQ1"
    assert scar_data["items"][0]["response_mode"] == "eight_d"

    trial_response = await async_client.get(
        "/api/v1/problem-management/issues",
        headers=headers,
        params={
            "module_key": "new_product_quality",
            "problem_category_key": "DQ0",
            "unified_status": "responding",
        },
    )
    assert trial_response.status_code == 200
    trial_data = trial_response.json()
    assert trial_data["total"] == 1
    assert trial_data["items"][0]["source_type"] == "trial_issue"
    assert trial_data["items"][0]["problem_category_key"] == "DQ0"
    assert trial_data["items"][0]["response_mode"] == "eight_d"

    my_items_response = await async_client.get(
        "/api/v1/problem-management/issues",
        headers=headers,
        params={
            "only_assigned_to_me": True,
        },
    )
    assert my_items_response.status_code == 200
    my_items_data = my_items_response.json()
    assert my_items_data["total"] == 5
    assert {item["source_type"] for item in my_items_data["items"]} == {
        "audit_nc",
        "customer_complaint",
        "process_issue",
        "scar",
        "trial_issue",
    }

    actionable_items_response = await async_client.get(
        "/api/v1/problem-management/issues",
        headers=headers,
        params={
            "only_actionable_to_me": True,
        },
    )
    assert actionable_items_response.status_code == 200
    actionable_items_data = actionable_items_response.json()
    assert actionable_items_data["total"] == 5
    assert {item["source_type"] for item in actionable_items_data["items"]} == {
        "audit_nc",
        "customer_complaint",
        "process_issue",
        "scar",
        "trial_issue",
    }

    created_by_me_response = await async_client.get(
        "/api/v1/problem-management/issues",
        headers=headers,
        params={
            "only_created_by_me": True,
        },
    )
    assert created_by_me_response.status_code == 200
    created_by_me_data = created_by_me_response.json()
    assert created_by_me_data["total"] == 5
    assert {item["source_type"] for item in created_by_me_data["items"]} == {
        "audit_nc",
        "customer_complaint",
        "process_issue",
        "scar",
        "trial_issue",
    }


@pytest.mark.asyncio
async def test_get_problem_management_issue_summaries_filters_only_overdue_items(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_user: User,
    test_user_token: str,
):
    headers = {"Authorization": f"Bearer {test_user_token}"}

    audit_nc = await _seed_audit_nc(
        db_session,
        user=test_user,
        audit_type="system_audit",
        name_suffix="overdue-audit",
        verification_status="open",
    )
    audit_nc.deadline = datetime.utcnow() - timedelta(days=1)

    process_issue = await _seed_process_issue(
        db_session,
        user=test_user,
        name_suffix="1101",
        process_id="ASSY-TEST-02",
        line_id="LINE-ASSY-02",
        issue_description="verification overdue process issue should stay visible in overdue view",
        issue_status=ProcessIssueStatus.IN_VERIFICATION,
    )
    process_issue.verification_end_date = (datetime.utcnow() - timedelta(days=1)).date()

    scar = await _seed_scar(
        db_session,
        user=test_user,
        name_suffix="3101",
        material_code="PCB-CONN-OVERDUE",
        defect_description="electronic component overdue scar should stay visible",
        scar_status=SCARStatus.UNDER_REVIEW,
    )
    scar.deadline = datetime.utcnow() - timedelta(days=1)

    trial_issue = await _seed_trial_issue(
        db_session,
        user=test_user,
        name_suffix="2101",
        issue_description="trial issue overdue should stay visible in overdue view",
        issue_status=IssueStatus.IN_PROGRESS,
    )
    trial_issue.deadline = datetime.utcnow() - timedelta(days=1)

    await db_session.commit()

    response = await async_client.get(
        "/api/v1/problem-management/issues",
        headers=headers,
        params={
            "only_overdue": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 4
    assert {item["source_type"] for item in data["items"]} == {
        "audit_nc",
        "process_issue",
        "scar",
        "trial_issue",
    }
    assert all(item["is_overdue"] is True for item in data["items"])


@pytest.mark.asyncio
async def test_scar_8d_submission_reassigns_review_action_to_internal_creator(
    db_session: AsyncSession,
    test_user: User,
):
    now = datetime.utcnow()
    auth_strategy = LocalAuthStrategy()

    supplier = Supplier(
        name="Supplier review action",
        code="SUP-REVIEW-ACTION",
        contact_person="Supplier QA",
        contact_email="supplier-review-action@example.com",
        contact_phone="13800000001",
        status=SupplierStatus.ACTIVE,
        created_at=now,
        updated_at=now,
        created_by=test_user.id,
        updated_by=test_user.id,
    )
    db_session.add(supplier)
    await db_session.flush()

    supplier_user = User(
        username="problem-supplier-review-action",
        password_hash=auth_strategy.hash_password("Test@1234"),
        full_name="Problem Supplier Review Action",
        email="problem-supplier-review-action@example.com",
        phone="13800138002",
        user_type=UserType.SUPPLIER,
        status=UserStatus.ACTIVE,
        supplier_id=supplier.id,
        password_changed_at=now,
        created_at=now,
        updated_at=now,
    )
    db_session.add(supplier_user)
    await db_session.flush()

    scar = SCAR(
        scar_number="SCAR-20260424-8801",
        supplier_id=supplier.id,
        material_code="PCB-REVIEW-001",
        defect_description="submitted 8D should return to internal reviewer",
        defect_qty=3,
        severity=SCARSeverity.HIGH,
        status=SCARStatus.OPEN,
        current_handler_id=supplier_user.id,
        deadline=now + timedelta(days=3),
        created_at=now,
        updated_at=now,
        created_by=test_user.id,
        updated_by=test_user.id,
    )
    db_session.add(scar)
    await db_session.commit()
    await db_session.refresh(scar)

    await EightDService.submit_8d_report(
        db=db_session,
        scar_id=scar.id,
        eight_d_data=EightDSubmit(
            d0_d3_data={"problem_description": "supplier-side containment completed"},
            d4_d7_data={
                "root_cause": "fixture wear caused unstable connector soldering",
                "corrective_action": "replace fixture and verify soldering parameters",
                "preventive_action": "add fixture maintenance frequency check",
            },
            d8_data={"horizontal_deployment": "extend to similar connector fixtures"},
        ),
        submitted_by=supplier_user.id,
        current_user=supplier_user,
    )

    await db_session.refresh(scar)
    assert scar.status == SCARStatus.UNDER_REVIEW
    assert scar.current_handler_id == test_user.id
