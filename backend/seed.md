# Seed Data Script

Management command to generate realistic test data for development and testing.

## Quick Start

```bash
cd backend
source venv/bin/activate

# Basic usage (creates 1 org with default counts)
python manage.py seed_data --email admin@example.com
```

## Full Options

```bash
python manage.py seed_data \
    --email admin@example.com \     # Required: Admin user email
    --orgs 2 \                      # Number of orgs (default: 1)
    --users-per-org 5 \             # Users per org (default: 3)
    --leads 50 \                    # Leads per org (default: 20)
    --accounts 20 \                 # Accounts per org (default: 10)
    --contacts 30 \                 # Contacts per org (default: 15)
    --opportunities 15 \            # Opportunities per org (default: 10)
    --cases 10 \                    # Cases per org (default: 5)
    --tasks 25 \                    # Tasks per org (default: 10)
    --teams 3 \                     # Teams per org (default: 2)
    --tags 10 \                     # Tags per org (default: 5)
    --seed 42 \                     # Random seed for reproducibility
    --password mypassword \         # Password for new users (default: testpass123)
    --clear \                       # Clear existing CRM data before seeding
    --no-input                      # Skip confirmation prompts
```

## Examples

```bash
# Create 2 organizations with lots of data
python manage.py seed_data --email admin@example.com --orgs 2 --leads 100 --accounts 50

# Reproducible seeding (same data every time)
python manage.py seed_data --email admin@example.com --seed 42

# Clear all CRM data and reseed
python manage.py seed_data --email admin@example.com --clear --no-input

# Minimal data for quick testing
python manage.py seed_data --email admin@example.com --leads 5 --accounts 3 --contacts 5 --opportunities 3 --cases 2 --tasks 5
```

## Features

- **Realistic data** - Uses Faker library for names, companies, emails, addresses, etc.
- **Weighted status distributions** - Simulates realistic data:
  - Leads: 40% assigned, 30% in process, 15% converted, 10% recycled, 5% closed
  - Opportunities: 20% each open stage, 10% closed won, 10% closed lost
  - Cases: 40% new, 25% assigned, 20% pending, 10% closed, 5% rejected
  - Tasks: 30% new, 40% in progress, 30% completed
- **Proper relationships**:
  - Accounts linked to contacts
  - Opportunities linked to accounts
  - Cases linked to accounts
  - Tasks linked to ONE parent (account/opportunity/case/lead)
  - Leads optionally linked to contacts
- **M2M assignments** - Each entity gets:
  - 1-2 assigned profiles
  - 0-1 team (70% chance)
  - 0-3 tags (60% chance)
- **Multi-tenancy** - Admin user gets profile in ALL created orgs
- **Reproducible** - Use `--seed` for deterministic data generation

## Clear Data Behavior

When using `--clear`:
- Deletes: Tasks, Cases, Opportunities, Leads, Accounts, Contacts, Teams, Tags
- Preserves: Users, Profiles, Organizations

This allows you to reseed CRM data without losing user accounts.

## Sample Output

```
$ python manage.py seed_data --email admin@test.com --orgs 2 --seed 42

Seeding CRM database...
Using seed: 42

--- Organization 1/2 ---
  Created org: Acme Corporation (USD, US)
  Created 4 profiles (1 admin, 3 users)
  Created 2 teams
  Created 5 tags
  Created 15 contacts
  Created 10 accounts
  Created 20 leads
  Created 10 opportunities
  Created 5 cases
  Created 10 tasks

--- Organization 2/2 ---
  Created org: Global Tech Inc (EUR, DE)
  Created 4 profiles (1 admin, 3 users)
  Created 2 teams
  Created 5 tags
  Created 15 contacts
  Created 10 accounts
  Created 20 leads
  Created 10 opportunities
  Created 5 cases
  Created 10 tasks

Seeding complete!

Summary:
  Organizations: 2
  Users: 7
  Profiles: 8
  Teams: 4
  Tags: 10
  Contacts: 30
  Accounts: 20
  Leads: 40
  Opportunities: 20
  Cases: 10
  Tasks: 20

Total time: 1.22 seconds
```

## Dependencies

The script requires the `faker` package (already in requirements.txt):

```bash
pip install faker
```
