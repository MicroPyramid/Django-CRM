# blocker
* data migration
* rls (row level security) db security

# after going live
* remove migrate_from_prisma once everything is good after going live.
* rls setup and check status
* we need to implement google login for /dashboard instead of password login. that is more secure and user friendly.
* remove /admin route and disable admin site because we are developing our custom management interface at /dashboard.
* configure aws ses
* list all emails going out and enhance templates, test every link in every email temaplate, test in live.
* how to suppress /favicon.ico requests for api.bottlecrm.io in nginx

* handle aws ses bounces
* blog
* UI enhance to look like twenty, notion
* task kanban
* invoices
* form builder to create registration/contact forms to collect leads in org
* work on dashboard UI like https://twenty.com/
* work on /docs for user docs and developer docs like twenty.com
* work on the website pages with inspiration from https://twenty.com/
* identify missing features compared to twentycrm
* custom fields
* org config to set default currency and country, those should be preloaded everywhere then.
* recent activities empty in http://localhost:5173/app. we need to see djago api and implement it if possible or else plan it.


i am developing crm with djangorestframework(api) + sveltekit (ui). it is good at mvp stage. now, i am thinking of multi tenant model like twenty crm. see our way of maanging org separation in postgres and tell me if we are aligned with twenty crm way of workspace


python manage.py migrate_from_prisma \
      --db-host=localhost \
      --db-name=prisma_crm_live \
      --db-user=postgres \
      --db-password=A2k-snQNR32Tbkq_wuddq2PpW5i-eh2
