Django-CRM
==========

Django CRM is opensource CRM developed on django framework. It has all the basic features of CRM to start with. We welcome code contributions and feature requests via github.

.. list-table::
   :header-rows: 1
   :widths: 50 50 150 90
   :stub-columns: 1

   *  -  Build Status
      -  Codacy
      -  Docker
      -  Support
   *  -   .. image:: https://travis-ci.org/MicroPyramid/Django-CRM.svg?branch=master
             :target: https://travis-ci.org/MicroPyramid/Django-CRM
             :alt: Travis

          .. image:: https://landscape.io/github/MicroPyramid/Django-CRM/master/landscape.svg?style=flat
             :target: https://landscape.io/github/MicroPyramid/Django-CRM/master
             :alt: Code Health

      -  .. image:: https://api.codacy.com/project/badge/Grade/b11da5f09dd542479fd3bd53944595d2
            :target: https://app.codacy.com/project/ashwin/Django-CRM/dashboard
            :alt: Codacy Dashboard
         .. image:: https://coveralls.io/repos/github/MicroPyramid/Django-CRM/badge.svg?branch=master
            :target: https://coveralls.io/github/MicroPyramid/Django-CRM?branch=master
            :alt: Codacy Coverage

      -  .. image:: https://img.shields.io/docker/automated/micropyramid/django-crm.svg
            :target: https://github.com/MicroPyramid/Django-CRM
            :alt: Docker Automated
         .. image:: https://img.shields.io/docker/build/micropyramid/django-crm.svg
            :target: https://github.com/MicroPyramid/Django-CRM
            :alt: Docker Build Passing
         .. image:: https://img.shields.io/docker/stars/micropyramid/django-crm.svg
            :target: https://hub.docker.com/r/micropyramid/django-crm/
            :alt: Docker Stars
         .. image:: https://img.shields.io/docker/pulls/micropyramid/django-crm.svg
            :target: https://hub.docker.com/r/micropyramid/django-crm/
            :alt: Docker Pulls

      -  .. image:: https://badges.gitter.im/Micropyramid/Django-CRM.png
            :target: https://gitter.im/MicroPyramid/Django-CRM
            :alt: Gitter
         .. image:: https://www.codetriage.com/micropyramid/django-crm/badges/users.svg
            :target: https://www.codetriage.com/micropyramid/django-crm
            :alt: Code Helpers
         .. image:: https://img.shields.io/github/license/MicroPyramid/Django-CRM.svg
            :target: https://pypi.python.org/pypi/Django-CRM/
         .. image:: https://opencollective.com/django-crm/backers/badge.svg
            :alt: Backers on Open Collective
            :target: #backers
         .. image:: https://opencollective.com/django-crm/sponsors/badge.svg
            :alt: Sponsors on Open Collective
            :target: #sponsors


http://django-crm.readthedocs.io for latest documentation


This project contains the following modules.

   * Contacts
   * Accounts
   * Cases
   * Leads
   * Opportunity
   * Planner


Try
===

Demo Available `here`_.

Demo credentials for Django CRM:

  * **Email:** admin@micropyramid.com
  * **Password:** admin


Installation
============

* Install the dependencies

   .. code-block:: python

      pip install -r requirements.txt
      cp crm/local_settings.example crm/local_settings.py
      python manage.py makemigrations
      python manage.py createsuperuser
      python manage.py runserver

  This will install all the required dependencies for django-crm.

  Then update the local_settings.py file with your email host server credentials.

   .. code-block:: python

      EMAIL_HOST = <your email host>
      EMAIL_HOST_USER = <your username>
      EMAIL_HOST_PASSWORD = <your password>

  These settings allow django-crm to send emails.
  After this download and install the System Requirements.


System Requirements
===================

- wkhtmltopdf (https://wkhtmltopdf.org/downloads.html)
- sass (https://www.npmjs.com/package/sass) or (https://rubygems.org/gems/sass)

Community
=========

Get help or stay up to date.

- [Contribute on Issues](https://github.com/MicroPyramid/Django-CRM/issues)
- Follow [@micropyramid](https://twitter.com/micropyramid) on Twitter
- Ask questions on [Stack Overflow](https://stackoverflow.com/questions/tagged/django-crm)
- Chat with community [Gitter](https://gitter.im/MicroPyramid/Django-CRM)
- For customisations, email django-crm@micropyramid.com

Credits
+++++++

Contributors
------------

This project exists thanks to all the people who contribute!

.. image:: https://opencollective.com/django-crm/contributors.svg?width=890&button=false

Backers
-------

Thank you to all our backers! `Become a backer`__.

.. image:: https://opencollective.com/django-crm/backers.svg?width=890
    :target: https://opencollective.com/django-crm#backers

__ Backer_
.. _Backer: https://opencollective.com/django-crm#backer

Sponsors
--------

Support us by becoming a sponsor. Your logo will show up here with a link to your website. `Become a sponsor`__.

.. image:: https://opencollective.com/django-crm/sponsor/0/avatar.svg
    :target: https://opencollective.com/django-crm/sponsor/0/website

__ Sponsor_
.. _Sponsor: https://opencollective.com/django-crm#sponsor



Feature requests and bug reports
================================
We welcome your feedback and support, raise github issue if you want to report a bug or request new feature. we are glad to help.

Need additional commercial support? `Contact us here`_

.. _contact us here: https://micropyramid.com/contact-us/

.. _here: https://django-crm.micropyramid.com/
