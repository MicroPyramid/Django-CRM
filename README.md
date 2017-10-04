# Django-CRM

.. image:: https://travis-ci.org/MicroPyramid/Django-CRM.svg?branch=master
   :target: https://travis-ci.org/MicroPyramid/Django-CRM

.. image:: https://img.shields.io/pypi/dm/Django-CRM.svg
    :target: https://pypi.python.org/pypi/Django-CRM
    :alt: Downloads

.. image:: https://img.shields.io/pypi/v/Django-CRM.svg
    :target: https://pypi.python.org/pypi/Django-CRM
    :alt: Latest Release

.. image:: https://coveralls.io/repos/github/MicroPyramid/Django-CRM/badge.svg?branch=master
   :target: https://coveralls.io/github/MicroPyramid/Django-CRM?branch=master

.. image:: https://landscape.io/github/MicroPyramid/Django-CRM/master/landscape.svg?style=flat
   :target: https://landscape.io/github/MicroPyramid/Django-CRM/master
   :alt: Code Health

.. image:: https://img.shields.io/github/license/MicroPyramid/Django-CRM.svg
    :target: https://pypi.python.org/pypi/Django-CRM/


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
