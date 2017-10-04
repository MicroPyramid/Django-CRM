Django-CRM's documentation:
=====================================

Introduction:
=============

Django-CRM provides a dashboard where you can manage customers at sales of the organization. It Provides to manage leads information and its activity, track issues from leads, contacts to send emails.

Source Code is available in Micropyramid Repository(https://github.com/MicroPyramid/Django-CRM.git).

Modules used:

    * Python  >= 2.6 (or Python 3.4)
    * Django  = 1.9.6
    * JQuery  >= 1.7


Installation
------------

1. Install Django-CRM from pip using the following command::

```
    pip install Django-CRM
            (or)
    git clone git@github.com:MicroPyramid/Django-CRM.git
    cd Django-CRM
    python setup.py install
```

2. Add the following in settings.py::

```
    # import at the top
    from django_crm import CRM_APPS
    # below INSTALLED_APPS setting
    INSTALLED_APPS += CRM_APPS
```

3. Include the Django-CRM urls in your urls.py::

```
    urlpatterns = [
        # ...........
        url(r'^admin/', admin.site.urls),
        url(r'^', include('django_crm.urls')),
        # ...........
    ]
```

4. If you cloned the package from git use virtualenv to install requirements::

```
    pip install -r requirements.txt
```

You can try it by hosting on your own or deploy to Heroku with a button click.

Deploy To Heroku:
[![heroku deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/MicroPyramid/Django-CRM)

Visit our Django web development page [Here](https://micropyramid.com/django-ecommerce-development/)


We welcome your feedback and support, raise github ticket if you want to report a bug. Need new features? `Contact us here`_

.. _contact us here: https://micropyramid.com/contact-us/

    or

mailto:: "hello@micropyramid.com"