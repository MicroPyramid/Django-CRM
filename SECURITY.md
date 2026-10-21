# Security policy

## Reporting a vulnerability

Report it privately through [GitHub's private vulnerability reporting](https://github.com/django-crm/Django-CRM/security/advisories/new). If you cannot use GitHub, email hello@bottlecrm.io with "Security" in the subject line.

Please do not open a public issue, pull request or discussion about it. Test only against your own self-hosted instance or your own organization, never against other people's data on the hosted service.

Include what you can:

- the affected part (API, web app or mobile app) and its version
- steps to reproduce, or a proof of concept
- the impact: what an attacker gains, and what access they need first

## Scope

We most want to hear about anything that lets one user act as another, read or change another organization's data, or gain admin or superadmin rights. Tenant isolation rests on explicit organization filters and on PostgreSQL row-level security, so a bypass of either is in scope.

## Supported versions

Fixes ship in the next release of the `django-crm` package and the `ghcr.io/django-crm/bottlecrm-frontend` image. Only the latest release receives security fixes.
