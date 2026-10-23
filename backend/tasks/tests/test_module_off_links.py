"""A task's deal, ticket or lead while that module is off: an edit that omits the
link or sends null keeps it, so a client that sends back what it loaded never
erases a hidden link."""

import pytest

from cases.models import Case
from common.testing import set_modules_off
from leads.models import Lead
from opportunity.models import Opportunity
from tasks.models import Task

LINKS = [
    pytest.param(
        "opportunity",
        "deals",
        lambda org: Opportunity.objects.create(org=org, name="Deal", stage=""),
        id="deal",
    ),
    pytest.param(
        "case",
        "tickets",
        lambda org: Case.objects.create(
            org=org, name="Ticket", status="New", priority="Normal"
        ),
        id="ticket",
    ),
    pytest.param(
        "lead",
        "leads",
        lambda org: Lead.objects.create(org=org, title="Lead", first_name="Lee"),
        id="lead",
    ),
]


@pytest.mark.parametrize(("field", "module", "make"), LINKS)
@pytest.mark.parametrize("verb", ["patch", "put"])
def test_a_task_keeps_its_hidden_link_on_edit(
    admin_client, org_a, field, module, make, verb
):
    parent = make(org_a)
    task = Task.objects.create(
        org=org_a, title="Follow up", status="New", priority="Medium", **{field: parent}
    )
    set_modules_off(org_a, module)

    for extra in ({}, {field: None}):
        response = getattr(admin_client, verb)(
            f"/api/tasks/{task.id}/",
            {"title": "Renamed", "status": "New", "priority": "Medium", **extra},
            format="json",
        )
        assert response.status_code == 200, response.content
        task.refresh_from_db()
        assert getattr(task, f"{field}_id") == parent.id
        assert task.title == "Renamed"


@pytest.mark.parametrize(("field", "module", "make"), LINKS)
def test_a_task_link_clears_on_null_while_its_module_is_on(
    admin_client, org_a, field, module, make
):
    task = Task.objects.create(
        org=org_a,
        title="Follow up",
        status="New",
        priority="Medium",
        **{field: make(org_a)},
    )

    response = admin_client.patch(
        f"/api/tasks/{task.id}/", {field: None}, format="json"
    )

    assert response.status_code == 200, response.content
    task.refresh_from_db()
    assert getattr(task, f"{field}_id") is None


@pytest.mark.parametrize(("field", "module", "make"), LINKS)
def test_a_task_cannot_be_created_with_an_off_module_record(
    admin_client, org_a, field, module, make
):
    parent = make(org_a)
    set_modules_off(org_a, module)

    response = admin_client.post(
        "/api/tasks/",
        {"title": "New", "status": "New", "priority": "Medium", field: str(parent.id)},
        format="json",
    )

    assert response.status_code == 400, response.content
    assert "is switched off for this organization." in str(
        response.json()["errors"][field]
    )
    assert not Task.objects.filter(org=org_a).exists()


@pytest.mark.parametrize(("field", "module", "make"), LINKS)
def test_a_task_edit_naming_another_off_module_record_is_refused(
    admin_client, org_a, field, module, make
):
    stored, other = make(org_a), make(org_a)
    task = Task.objects.create(
        org=org_a, title="Follow up", status="New", priority="Medium", **{field: stored}
    )
    set_modules_off(org_a, module)

    refused = admin_client.patch(
        f"/api/tasks/{task.id}/", {field: str(other.id)}, format="json"
    )
    resent = admin_client.patch(
        f"/api/tasks/{task.id}/",
        {field: str(stored.id), "title": "Same"},
        format="json",
    )

    assert refused.status_code == 400, refused.content
    assert resent.status_code == 200, resent.content
    task.refresh_from_db()
    assert getattr(task, f"{field}_id") == stored.id
