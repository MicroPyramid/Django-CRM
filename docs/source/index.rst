==========
Django CRM
==========

Introduction:
=============

Django CRM is opensourse CRM developed on django framework. It has all the basic features of CRM to start with. We welcome code contributions and feature requests via github.

Source Code is available in Micropyramid Repository() `Link <https://github.com/MicroPyramid/Django-CRM.git>`_.

Tech stack used:
================

* Python >= 3.4
* Django >= 2.0
* Redis
* django-simple-pagination

Modules available in Django-CRM:
================================

User functionalites:
********************
.. toctree::
   :maxdepth: 2

   Login
   Forget Password
   Profile
   Change Password


Modules in crm:
***************

.. toctree::
  :maxdepth: 2

  Accounts
  Contacts
  Leads
  Opportunity
  Cases
  Documents

Rules to follow:-
=================
|  1.writing test cases for the code
|  2.test cases coverage percent should be above 90%



Setup On Local System
=====================

On Windows
**********

On Ubuntu
*********
|  First Create a Virtual Environment in a local directory.
|  Install Pip to install python packages.
|  Then clone the source code from the repository `click here <https://github.com/MicroPyramid/Django-CRM.git>`_.
|  Activate Virtual environment, then install the requirements.txt using the command 

::

  pip install -r requirements.txt

|  Then execute 

::

  python manage.py runserver

Now Go to browser, enter the url ``http://127.0.0.1:8000``

Installation - Requirements
===========================


Ubuntu 64bit - 16.04
*********************

|  $ sudo apt-get update && apt-get upgrade -y
|  $ sudo apt-get install -y curl wget libpq-dev python3-dev gem ruby ruby-dev build-essential libssl-dev libffi-dev python-dev python-virtualenv python-pip git redis-server libtiff5-dev libjpeg8-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev libharfbuzz-dev libfribidi-dev tcl8.6-dev tk8.6-dev python-tk
|  $ sudo gem install sass

Visit our Django web development page [Here](https://micropyramid.com/django-ecommerce-development/)


We welcome your feedback and support, raise github ticket if you want to report a bug or need new feature.

Need additional support? `Contact us here`_

.. _contact us here: https://micropyramid.com/contact-us/

    or

mailto:: "hello@micropyramid.com"


