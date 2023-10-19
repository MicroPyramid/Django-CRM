==========
Django CRM
==========

Introduction:
=============

Django CRM is an Open Source CRM developed on the Django framework. It has all the basic features of CRM to start with. We welcome code contributions and feature requests via Github.

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
|  First, create a Virtual Environment in a local directory.
|  Install Pip to install python packages.
|  Then clone the source code from the repository `click here <https://github.com/MicroPyramid/Django-CRM.git>`_.
|  Activate Virtual environment, then install the requirements.txt using the command 

::

  pip install -r requirements.txt

|  Then execute 

::

  python manage.py runserver

Now, open your browser and enter the url ``http://127.0.0.1:8000``

Installation - Requirements
===========================


Ubuntu 64bit - 16.04
*********************

|  $ sudo apt-get update && apt-get upgrade -y
|  $ sudo apt-get install -y curl wget libpq-dev python3-dev gem ruby ruby-dev build-essential libssl-dev libffi-dev python-dev python-virtualenv python-pip git redis-server libtiff5-dev libjpeg8-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev libharfbuzz-dev libfribidi-dev tcl8.6-dev tk8.6-dev python-tk
|  $ sudo gem install sass

Visit our Django web development page [Here](https://micropyramid.com/django-ecommerce-development/)


Docker
*********************

To install using Docker, you need to have Docker installed in your system.

1. Clone the repository into your system.

2. Then run the following commands to build and run the container:

   | $ docker build -t djcrm:1 -f docker/Dockerfile .
   | $ docker-compose -f docker/docker-compose.yml up
 
 The first line will build your container image and the second one will run it.
 
 There you will be able to see what is going on inside the container.
 
 If you head to localhost:8000/admin you will get to the admin panel of Wagtail.
 
 3. In order to be able to login to the admin panel you have to create an admin user. If you are using VSCode, go to the bottom left corner and click on it, there go to "Attach to running container" and you will see two options, click on the one called "crm-app". Once inside the container, then cd into the app directory and run:
 
  | $ python3 manage.py createsuperuser
  
  After this you will be able to log into the admin panel with the user you just created.

We welcome your feedback and support, raise github ticket if you want to report a bug or need new feature.

Need additional support? `Contact us here`_

.. _contact us here: https://micropyramid.com/contact-us/

    or

mailto:: "hello@micropyramid.com"


