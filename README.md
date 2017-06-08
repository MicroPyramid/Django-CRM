# Django-CRM

Installation
--------------

1. Install Django-CRM using the following command::
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

We welcome your feedback and support, raise github ticket if you want to report a bug. Need new features?
[_contact us here](https://micropyramid.com/contact-us/)
