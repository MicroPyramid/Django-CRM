Django-CRM
==========

Django CRM is opensource CRM developed on django framework. It has all
the basic features of CRM to start with. We welcome code contributions
and feature requests via github.

http://django-crm.readthedocs.io for latest documentation

This project contains the following modules:

    -  Contacts
    -  Accounts
    -  Invoices
    -  Cases
    -  Leads
    -  Opportunity
    -  Planner

## Try for free `here <https://bottlecrm.com/>`__
-------------------------------------------------

Installation
============

We recommend ubuntu 18.04 or ubuntu 20.04. These instructions are
verified for ubuntu 20.04.

#### System Requirements
------------------------

::

    sudo apt install postgresql xvfb libfontconfig wkhtmltopdf git libpq-dev python3-dev python3-pip gem ruby ruby-dev build-essential libssl-dev libffi-dev python3-venv redis-server redis-tools virtualenv -y

    sudo gem install sass

    sudo apt-get install postfix

postfix package installation process
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

-  After running ``sudo apt-get install postfix`` in terminal, select
   ``Internet`` as a configuration from the pop-up and click ok. Next it
   will ask to enter the ``System mail name`` which will be the used as
   a ``From Email Address`` during sending the mail.

#### Install dependencies
-------------------------

-  Create and activate a virtual environment.

::

    virtualenv venv
    source venv/bin/activate

-  Install the project's dependencie

::

    pip install -r requirements.txt

env variables
^^^^^^^^^^^^^

-  Then refer to ``env.md`` for environment variables and keep those in
   the ``.env`` file in the current folder as your project is in.
-  Add ``127.0.0.1   test.localhost`` to your hosts file ``/etc/hosts``.
   Then you can use test as company name to register and login.

next steps
^^^^^^^^^^

::

    python manage.py migrate
    python manage.py runserver

Then open http://localhost:8000 in your borwser and create a new account
with test as company name. We mapped ``test.localhost`` to
``127.0.0.1``. So, it should work properly.

To edit content
~~~~~~~~~~~~~~~

::

    python manage.py create_blog_user 'username'

The above command will add the user as blog admin to edit content at
/blog/admin/

Useful tools and packages
~~~~~~~~~~~~~~~~~~~~~~~~~

::

    pipdeptree # to see pip dependancy tree
    black # to format code to meet python coding standards
    pip-check -H  # to see upgradable packages

Community
=========

Get help or stay up to date.

-  `Issues <https://github.com/MicroPyramid/Django-CRM/issues>`__
-  Follow [@micropyramid](https://twitter.com/micropyramid) on Twitter
-  Ask questions on `Stack
   Overflow <https://stackoverflow.com/questions/tagged/django-crm>`__
-  Chat with community
   `Gitter <https://gitter.im/MicroPyramid/Django-CRM>`__
-  For customisations, email to django-crm@micropyramid.com

Credits
-------

Contributors
============

This project exists thanks to all the people who contribute!

.. figure:: https://opencollective.com/django-crm/contributors.svg?width=890&button=false
   :alt: image

Feature requests and bug reports
================================

We welcome your feedback and support, raise github issue if you want to
report a bug or request new feature. we are glad to help.

For commercial support `Contact
us <https://micropyramid.com/contact-us/>`__
