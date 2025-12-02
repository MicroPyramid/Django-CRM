
# after going live
* rls (row level security) db security
* rls setup and check status
* configure aws ses
* list all emails going out and enhance templates, test every link in every email temaplate, test in live.

# repeat
* identify security issues and fix them. issues can be in the way we are handling user authentication and authorization. issues can be in rls. issues can be in the way we are handling user roles and permissions. issues can be in middleware where we are checking user permissions in org level.


# tasks

review all comments in python code to decide wethere to keep or remove. there are a lot old comments useless or unnecessary.

* we have http://localhost:5173/notion empty page to create notion like table with column visibility to show/hide columns. create it with mock data, no back coding needed. used shadcn if needed or implement it using tailwind.

* we need to enhance the leads list page table to look like /notion table.

* look into contact, opportunity, account, lead, task, case models and review to finalize their feilds. then sync all the fields with backend api and the frontend.

* in account details, when we click on add contact, it should open the contact create form to add the contact to the account right?
* in account details, when we click on add opportunity, it should open the opportunity create form to add the opportunity to the account right?

* opportunities kanban in not working. we need to see the api and implement it if possible or else plan it. need complete implementation of opportunities kanban.


* excel like creation of leads, contacts, opportunities, tasks, deals, etc and option to open the detailed form to edit or create like notion. start with tasks and do every other entity.
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
