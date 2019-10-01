Installation & Configuration
============================

1. Create a django-crm directory using mkdir, move to it using cd

   .. code-block:: python

		mkdir django-crm
		cd django-crm

2. install virtualenv using the following command

   .. code-block:: python

		sudo apt-get install virtualenv

3. create a python3 virtual environment and activate it using the following command

   .. code-block:: python

		virtualenv -p python3 env
		source ../env/bin/activate

4. create a django-crm directory again, move to it using cd

   .. code-block:: python

		mkdir django-crm
		cd django-crm

5. Install git using the following command and configure the account details

   .. code-block:: python

		sudo apt-get install git


   .. code-block:: python

		git config --user.email <your email id>
		git config --user.name  <your name>

6. Intialize the git using the following command

   .. code-block:: python

   		git init


7. Add django-crm repository using the following command

   .. code-block:: python

		git remote add origin https://github.com/MicroPyramid/Django-CRM.git

7. Pull the latest code of django-crm using the following command

   .. code-block:: python

		git pull origin master

8. Install project dependencies using the following commands

   .. code-block:: python

		curl -sL https://deb.nodesource.com/setup_10.x | bash - 
		sudo apt-get update
		sudo apt-get apt install -y ruby-dev nodejs postgresql-client redis-server wkhtmltopdf memcache
		gem install compass sass
		npm -g install less
		pip install --no-cache-dir redis
		pip install --no-cache-dir -r requirements.txt

9. We're using elasticsearch for searching emails in application. Install elasticsearch using the following command

   .. code-block:: python

		### Install Java 

		sudo add-apt-repository ppa:webupd8team/java
		sudo apt-get update
		sudo apt-get install oracle-java8-installer -y java -version

   .. code-block:: python

		### Download and install the Public Signing Key
		wget -qO - https://packages.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add - echo "deb https://packages.elastic.co/elasticsearch/2.x/debian stable main" | sudo tee -a /etc/apt/sources.list.d/elasticsearch-2.x.list

   .. code-block:: python

		### Install Elasticsearch 
		sudo apt-get update && sudo apt-get install elasticsearch -y
		# Start elasticsearch
		sudo service elasticsearch start


10. open postgresql shell and create a database in postgresql using the following command
	
   .. code-block:: python

		sudo su - postgres
		psql
		create database dj_crm;

11. we're loading third party related keys from virtual environment env. We need to add those keys to tun the application

		# sendgrid details
		
		SG_USER=<sendgrid username>
		SG_PWD=<sendgrid password>

		#google developers account details
		
		GP_CLIENT_ID=<oauth0 client id>
		GP_CLIENT_SECRET=<oauth0 client secret>
		ENABLE_GOOGLE_LOGIN=<variable to configure google login in application>

		#sentry details
		
		SENTRYDSN=<sentry project dsn>
		SENTRY_ENABLED=<variable to configure sentry in application>

		#aws account details

		AWSBUCKETNAME=<aws bucket name>
		AWS_ACCESS_KEY_ID=<aws access key id>
		AWS_SECRET_ACCESS_KEY=<aws access secret key>


12. Apply migrations to database using the following command

   .. code-block:: python

		python manage.py migrate

13. Create superuser using the following command

   .. code-block:: python

	python manage.py createsuperuser

	
	It'll ask for username, email, password for user


14. Run the application using the following command and open the browsr, visit http://localhost:8000

   .. code-block:: python

		python manage.py runserver


15. Use the following command for indexing documents in elasticsearch


   .. code-block:: python

   		python manage.py rebuild_idex

16. We're using celery for sending emails, other related tasks in the application. Run celery using the following commands

   .. code-block:: python
	
		celery -A crm worker -l info 

   .. code-block:: python

		celery -A crm beat -l info

