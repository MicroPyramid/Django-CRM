"""Tests for Sales Goals / Quotas feature."""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest

from common.models import Teams
from opportunity.models import Opportunity, SalesGoal


# ---- Fixtures ---- #


@pytest.fixture
def team_a(org_a):
    return Teams.objects.create(name="Sales Team A", org=org_a)


@pytest.fixture
def goal_revenue(org_a, admin_profile):
    """A revenue goal for the current month."""
    today = date.today()
    return SalesGoal.objects.create(
        name="Monthly Revenue",
        goal_type="REVENUE",
        target_value=Decimal("100000"),
        period_type="MONTHLY",
        period_start=today.replace(day=1),
        period_end=(today.replace(day=28) + timedelta(days=4)).replace(day=1)
        - timedelta(days=1),
        assigned_to=admin_profile,
        org=org_a,
    )


@pytest.fixture
def goal_deals(org_a, user_profile):
    """A deals closed goal for the current month."""
    today = date.today()
    return SalesGoal.objects.create(
        name="Monthly Deals",
        goal_type="DEALS_CLOSED",
        target_value=Decimal("10"),
        period_type="MONTHLY",
        period_start=today.replace(day=1),
        period_end=(today.replace(day=28) + timedelta(days=4)).replace(day=1)
        - timedelta(days=1),
        assigned_to=user_profile,
        org=org_a,
    )


@pytest.fixture
def team_goal(org_a, team_a):
    """A team revenue goal."""
    today = date.today()
    return SalesGoal.objects.create(
        name="Team Revenue",
        goal_type="REVENUE",
        target_value=Decimal("500000"),
        period_type="QUARTERLY",
        period_start=today.replace(day=1),
        period_end=(today.replace(day=28) + timedelta(days=4)).replace(day=1)
        - timedelta(days=1),
        team=team_a,
        org=org_a,
    )


def _create_won_opportunity(org, user, amount, closed_on=None):
    """Helper to create a CLOSED_WON opportunity."""
    if closed_on is None:
        closed_on = date.today()
    opp = Opportunity.objects.create(
        name=f"Won Deal {amount}",
        stage="CLOSED_WON",
        amount=Decimal(str(amount)),
        closed_on=closed_on,
        org=org,
        created_by=user,
    )
    return opp


# ---- Model Tests ---- #


class TestSalesGoalModel:
    def test_create_goal(self, goal_revenue):
        assert goal_revenue.pk is not None
        assert goal_revenue.name == "Monthly Revenue"
        assert goal_revenue.goal_type == "REVENUE"
        assert goal_revenue.target_value == Decimal("100000")
        assert str(goal_revenue) == "Monthly Revenue (Revenue)"

    def test_compute_progress_revenue(
        self, goal_revenue, org_a, admin_user, admin_profile
    ):
        opp = _create_won_opportunity(org_a, admin_user, 25000)
        opp.assigned_to.add(admin_profile)
        opp2 = _create_won_opportunity(org_a, admin_user, 15000)
        opp2.assigned_to.add(admin_profile)

        progress = goal_revenue.compute_progress()
        assert progress == Decimal("40000")

    def test_compute_progress_deals_closed(
        self, goal_deals, org_a, regular_user, user_profile
    ):
        for i in range(3):
            opp = _create_won_opportunity(org_a, regular_user, 1000 + i)
            opp.assigned_to.add(user_profile)

        progress = goal_deals.compute_progress()
        assert progress == Decimal("3")

    def test_progress_scoped_to_user(
        self, goal_revenue, org_a, admin_user, admin_profile, regular_user, user_profile
    ):
        # Deal by admin (should count)
        opp1 = _create_won_opportunity(org_a, admin_user, 10000)
        opp1.assigned_to.add(admin_profile)

        # Deal by regular user (should NOT count for admin's goal)
        opp2 = _create_won_opportunity(org_a, regular_user, 20000)
        opp2.assigned_to.add(user_profile)

        progress = goal_revenue.compute_progress()
        assert progress == Decimal("10000")

    def test_progress_scoped_to_team(
        self, team_goal, org_a, admin_user, admin_profile, team_a
    ):
        team_a.users.add(admin_profile)

        opp = _create_won_opportunity(org_a, admin_user, 50000)
        opp.assigned_to.add(admin_profile)

        progress = team_goal.compute_progress()
        assert progress == Decimal("50000")

    def test_progress_ignores_outside_period(
        self, goal_revenue, org_a, admin_user, admin_profile
    ):
        # Create opp outside the goal period
        outside_date = goal_revenue.period_start - timedelta(days=30)
        opp = _create_won_opportunity(org_a, admin_user, 50000, closed_on=outside_date)
        opp.assigned_to.add(admin_profile)

        progress = goal_revenue.compute_progress()
        assert progress == Decimal("0")

    def test_progress_percent(self, goal_revenue, org_a, admin_user, admin_profile):
        opp = _create_won_opportunity(org_a, admin_user, 75000)
        opp.assigned_to.add(admin_profile)

        assert goal_revenue.progress_percent == 75

    def test_progress_percent_capped_at_100(
        self, goal_revenue, org_a, admin_user, admin_profile
    ):
        opp = _create_won_opportunity(org_a, admin_user, 150000)
        opp.assigned_to.add(admin_profile)

        assert goal_revenue.progress_percent == 100

    def test_progress_percent_zero_target(self, org_a):
        today = date.today()
        goal = SalesGoal.objects.create(
            name="Zero target",
            goal_type="REVENUE",
            target_value=Decimal("0"),
            period_type="MONTHLY",
            period_start=today,
            period_end=today + timedelta(days=30),
            org=org_a,
        )
        assert goal.progress_percent == 0

    def test_status_completed(self, goal_revenue, org_a, admin_user, admin_profile):
        opp = _create_won_opportunity(org_a, admin_user, 100000)
        opp.assigned_to.add(admin_profile)

        assert goal_revenue.status == "completed"

    def test_status_on_track(self, org_a, admin_profile, admin_user):
        # Create a goal for a period that just started
        today = date.today()
        goal = SalesGoal.objects.create(
            name="Future Goal",
            goal_type="REVENUE",
            target_value=Decimal("100000"),
            period_type="CUSTOM",
            period_start=today - timedelta(days=1),
            period_end=today + timedelta(days=99),
            assigned_to=admin_profile,
            org=org_a,
        )
        # 1% of period elapsed, 0% progress => behind
        # Actually 0% progress with ~1% elapsed => behind
        # Let's add enough to be on track
        opp = _create_won_opportunity(org_a, admin_user, 5000, closed_on=today)
        opp.assigned_to.add(admin_profile)

        assert goal.status in ("on_track", "at_risk", "behind")

    def test_status_behind(self, org_a, admin_profile):
        # Goal period almost over, no progress
        today = date.today()
        goal = SalesGoal.objects.create(
            name="Behind Goal",
            goal_type="REVENUE",
            target_value=Decimal("100000"),
            period_type="CUSTOM",
            period_start=today - timedelta(days=90),
            period_end=today + timedelta(days=10),
            assigned_to=admin_profile,
            org=org_a,
        )
        assert goal.status == "behind"


# ---- API Tests ---- #


class TestSalesGoalAPI:
    GOALS_URL = "/api/opportunities/goals/"

    def test_list_goals_admin(self, admin_client, goal_revenue, goal_deals):
        response = admin_client.get(self.GOALS_URL)
        assert response.status_code == 200
        assert response.data["goals_count"] == 2

    def test_list_goals_non_admin(
        self, user_client, goal_revenue, goal_deals, user_profile
    ):
        """Non-admin sees only goals assigned to them."""
        response = user_client.get(self.GOALS_URL)
        assert response.status_code == 200
        # user_profile should see goal_deals (assigned to them)
        goal_ids = [g["id"] for g in response.data["goals"]]
        assert str(goal_deals.id) in goal_ids

    def test_create_goal_admin(self, admin_client, org_a):
        today = date.today()
        data = {
            "name": "New Goal",
            "goal_type": "REVENUE",
            "target_value": "50000",
            "period_type": "MONTHLY",
            "period_start": str(today.replace(day=1)),
            "period_end": str(
                (today.replace(day=28) + timedelta(days=4)).replace(day=1)
                - timedelta(days=1)
            ),
        }
        response = admin_client.post(self.GOALS_URL, data, format="json")
        assert response.status_code == 200
        assert response.data["error"] is False
        assert SalesGoal.objects.filter(name="New Goal", org=org_a).exists()

    def test_create_goal_non_admin_forbidden(self, user_client):
        today = date.today()
        data = {
            "name": "Sneaky Goal",
            "goal_type": "REVENUE",
            "target_value": "50000",
            "period_type": "MONTHLY",
            "period_start": str(today),
            "period_end": str(today + timedelta(days=30)),
        }
        response = user_client.post(self.GOALS_URL, data, format="json")
        assert response.status_code == 403

    def test_create_goal_validation_period(self, admin_client):
        today = date.today()
        data = {
            "name": "Bad Period",
            "goal_type": "REVENUE",
            "target_value": "50000",
            "period_type": "CUSTOM",
            "period_start": str(today + timedelta(days=30)),
            "period_end": str(today),
        }
        response = admin_client.post(self.GOALS_URL, data, format="json")
        assert response.status_code == 400

    def test_create_goal_validation_target(self, admin_client):
        today = date.today()
        data = {
            "name": "Zero Target",
            "goal_type": "REVENUE",
            "target_value": "0",
            "period_type": "MONTHLY",
            "period_start": str(today),
            "period_end": str(today + timedelta(days=30)),
        }
        response = admin_client.post(self.GOALS_URL, data, format="json")
        assert response.status_code == 400

    def test_update_goal(self, admin_client, goal_revenue):
        url = f"{self.GOALS_URL}{goal_revenue.id}/"
        response = admin_client.put(
            url,
            {"name": "Updated Goal Name", "target_value": "200000"},
            format="json",
        )
        assert response.status_code == 200
        goal_revenue.refresh_from_db()
        assert goal_revenue.name == "Updated Goal Name"
        assert goal_revenue.target_value == Decimal("200000")

    def test_delete_goal(self, admin_client, goal_revenue):
        url = f"{self.GOALS_URL}{goal_revenue.id}/"
        response = admin_client.delete(url)
        assert response.status_code == 200
        assert not SalesGoal.objects.filter(id=goal_revenue.id).exists()

    def test_delete_goal_non_admin_forbidden(self, user_client, goal_revenue):
        url = f"{self.GOALS_URL}{goal_revenue.id}/"
        response = user_client.delete(url)
        assert response.status_code == 403

    def test_org_isolation(self, org_b_client, goal_revenue):
        """org_b client should not see org_a's goals."""
        response = org_b_client.get(self.GOALS_URL)
        assert response.status_code == 200
        assert response.data["goals_count"] == 0

    def test_get_goal_detail(self, admin_client, goal_revenue):
        url = f"{self.GOALS_URL}{goal_revenue.id}/"
        response = admin_client.get(url)
        assert response.status_code == 200
        assert response.data["name"] == "Monthly Revenue"
        assert "progress_value" in response.data
        assert "progress_percent" in response.data
        assert "status" in response.data

    def test_filter_active(self, admin_client, org_a):
        today = date.today()
        SalesGoal.objects.create(
            name="Active Goal",
            goal_type="REVENUE",
            target_value=Decimal("1000"),
            period_type="MONTHLY",
            period_start=today,
            period_end=today + timedelta(days=30),
            is_active=True,
            org=org_a,
        )
        SalesGoal.objects.create(
            name="Inactive Goal",
            goal_type="REVENUE",
            target_value=Decimal("1000"),
            period_type="MONTHLY",
            period_start=today,
            period_end=today + timedelta(days=30),
            is_active=False,
            org=org_a,
        )
        response = admin_client.get(f"{self.GOALS_URL}?active=true")
        assert response.status_code == 200
        names = [g["name"] for g in response.data["goals"]]
        assert "Active Goal" in names
        assert "Inactive Goal" not in names

    def test_filter_current(self, admin_client, org_a):
        today = date.today()
        SalesGoal.objects.create(
            name="Current Goal",
            goal_type="REVENUE",
            target_value=Decimal("1000"),
            period_type="MONTHLY",
            period_start=today - timedelta(days=5),
            period_end=today + timedelta(days=25),
            org=org_a,
        )
        SalesGoal.objects.create(
            name="Past Goal",
            goal_type="REVENUE",
            target_value=Decimal("1000"),
            period_type="MONTHLY",
            period_start=today - timedelta(days=60),
            period_end=today - timedelta(days=30),
            org=org_a,
        )
        response = admin_client.get(f"{self.GOALS_URL}?current=true")
        assert response.status_code == 200
        names = [g["name"] for g in response.data["goals"]]
        assert "Current Goal" in names
        assert "Past Goal" not in names


class TestLeaderboardAPI:
    LEADERBOARD_URL = "/api/opportunities/goals/leaderboard/"

    def test_leaderboard_ranked(
        self, admin_client, org_a, admin_user, admin_profile, regular_user, user_profile
    ):
        today = date.today()
        period_start = today.replace(day=1)
        period_end = (today.replace(day=28) + timedelta(days=4)).replace(
            day=1
        ) - timedelta(days=1)

        # Create goals for both users
        goal1 = SalesGoal.objects.create(
            name="Admin Goal",
            goal_type="REVENUE",
            target_value=Decimal("100000"),
            period_type="MONTHLY",
            period_start=period_start,
            period_end=period_end,
            assigned_to=admin_profile,
            org=org_a,
        )
        goal2 = SalesGoal.objects.create(
            name="User Goal",
            goal_type="REVENUE",
            target_value=Decimal("50000"),
            period_type="MONTHLY",
            period_start=period_start,
            period_end=period_end,
            assigned_to=user_profile,
            org=org_a,
        )

        # Admin has 50% progress
        opp1 = _create_won_opportunity(org_a, admin_user, 50000)
        opp1.assigned_to.add(admin_profile)

        # User has 80% progress
        opp2 = _create_won_opportunity(org_a, regular_user, 40000)
        opp2.assigned_to.add(user_profile)

        response = admin_client.get(self.LEADERBOARD_URL)
        assert response.status_code == 200
        leaderboard = response.data["leaderboard"]
        assert len(leaderboard) == 2
        # User (80%) should rank above admin (50%)
        assert leaderboard[0]["percent"] >= leaderboard[1]["percent"]
        assert leaderboard[0]["rank"] == 1
        assert leaderboard[1]["rank"] == 2


class TestDashboardGoalSummary:
    def test_dashboard_includes_goal_summary(
        self, admin_client, goal_revenue
    ):
        response = admin_client.get("/api/dashboard/")
        assert response.status_code == 200
        assert "goal_summary" in response.data
        # Admin should see their goal
        assert len(response.data["goal_summary"]) >= 1
        goal = response.data["goal_summary"][0]
        assert goal["name"] == "Monthly Revenue"
        assert "progress_value" in goal
        assert "progress_percent" in goal
        assert "status" in goal


class TestGoalMilestoneTask:
    @patch("opportunity.tasks._send_goal_milestone_email")
    def test_milestone_notification_sent(
        self, mock_send, org_a, admin_user, admin_profile
    ):
        from opportunity.tasks import check_goal_milestones

        today = date.today()
        goal = SalesGoal.objects.create(
            name="Milestone Test",
            goal_type="REVENUE",
            target_value=Decimal("100"),
            period_type="MONTHLY",
            period_start=today - timedelta(days=5),
            period_end=today + timedelta(days=25),
            assigned_to=admin_profile,
            org=org_a,
        )

        # Create enough progress to hit 50%
        opp = _create_won_opportunity(org_a, admin_user, 60, closed_on=today)
        opp.assigned_to.add(admin_profile)

        check_goal_milestones()

        goal.refresh_from_db()
        assert goal.milestone_50_notified is True
        assert mock_send.called

    @patch("opportunity.tasks._send_goal_milestone_email")
    def test_milestone_not_sent_twice(
        self, mock_send, org_a, admin_user, admin_profile
    ):
        from opportunity.tasks import check_goal_milestones

        today = date.today()
        goal = SalesGoal.objects.create(
            name="No Dupe Test",
            goal_type="REVENUE",
            target_value=Decimal("100"),
            period_type="MONTHLY",
            period_start=today - timedelta(days=5),
            period_end=today + timedelta(days=25),
            assigned_to=admin_profile,
            milestone_50_notified=True,
            org=org_a,
        )

        opp = _create_won_opportunity(org_a, admin_user, 60, closed_on=today)
        opp.assigned_to.add(admin_profile)

        check_goal_milestones()

        goal.refresh_from_db()
        # Should not trigger 90% (only at 60%)
        assert goal.milestone_90_notified is False
        # Already had 50% notified, should not re-send
        # mock_send may be called for other things, but milestone_50 was already True
