from accounts.models import Account
from cases.models import Case
from celery.task import task
from common.models import Document
from contacts.models import Contact
from events.models import Event
from leads.models import Lead
from opportunity.models import Opportunity
from tasks.models import Task
from teams.models import Teams


@task
def update_team_users(team_id):
    """ this function updates assigned_to field on all models when a team is updated """
    pass
    team = Teams.objects.filter(id=team_id).first()
    if team:
        teams_members = team.users.all()
        # for accounts
        accounts = team.account_teams.all()
        for account in accounts:
            account_assigned_to_users = account.assigned_to.all()
            for team_member in teams_members:
                if team_member not in account_assigned_to_users:
                    account.assigned_to.add(team_member)

        # for contacts
        contacts = team.contact_teams.all()
        for contact in contacts:
            contact_assigned_to_users = contact.assigned_to.all()
            for team_member in teams_members:
                if team_member not in contact_assigned_to_users:
                    contact.assigned_to.add(team_member)

        # for leads
        leads = team.lead_teams.all()
        for lead in leads:
            lead_assigned_to_users = lead.assigned_to.all()
            for team_member in teams_members:
                if team_member not in lead_assigned_to_users:
                    lead.assigned_to.add(team_member)

        # for opportunities
        opportunities = team.oppurtunity_teams.all()
        for opportunity in opportunities:
            opportunity_assigned_to_users = opportunity.assigned_to.all()
            for team_member in teams_members:
                if team_member not in opportunity_assigned_to_users:
                    opportunity.assigned_to.add(team_member)

        # for cases
        cases = team.cases_teams.all()
        for case in cases:
            case_assigned_to_users = case.assigned_to.all()
            for team_member in teams_members:
                if team_member not in case_assigned_to_users:
                    case.assigned_to.add(team_member)

        # for documents
        docs = team.document_teams.all()
        for doc in docs:
            doc_assigned_to_users = doc.assigned_to.all()
            for team_member in teams_members:
                if team_member not in doc_assigned_to_users:
                    doc.shared_to.add(team_member)

        # for tasks
        tasks = team.tasks_teams.all()
        for task in tasks:
            task_assigned_to_users = task.assigned_to.all()
            for team_member in teams_members:
                if team_member not in task_assigned_to_users:
                    task.assigned_to.add(team_member)

        # for invoices
        invoices = team.invoices_teams.all()
        for invoice in invoices:
            invoice_assigned_to_users = invoice.assigned_to.all()
            for team_member in teams_members:
                if team_member not in invoice_assigned_to_users:
                    invoice.assigned_to.add(team_member)

        # for events
        events = team.event_teams.all()
        for event in events:
            event_assigned_to_users = event.assigned_to.all()
            for team_member in teams_members:
                if team_member not in event_assigned_to_users:
                    event.assigned_to.add(team_member)