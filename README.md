# Django-CRM

============

Django CRM is opensource CRM developed on django framework. It has all
the basic features of CRM to start with. We welcome code contributions
and feature requests via github.

## Project Status and Future Direction

### Background

9 years ago, I launched this project with a mission to provide startups with a free, open-source, and customizable CRM solution, addressing the high subscription costs of commercial alternatives. Initially developed as a Django full-stack application, the project evolved significantly with the support of a dedicated team. However, maintaining the team and covering salaries depleted resources, and I was unable to renew the domain. Recognizing the need for a modernized user experience, I explored updating the frontend with React but ultimately faced financial and team constraints.

### Moving Forward

To align with the project’s vision and address these challenges, I’ve shifted development to a new repository using **SvelteKit** and **Prisma** for a robust, fast, and feature-rich framework. A Minimum Viable Product (MVP) was released last week at [MicroPyramid/opensource-startup-crm](https://github.com/MicroPyramid/opensource-startup-crm).

#### Key Updates:

-   **Current Repository:** No further updates will be made to this repository.
    
-   **New Repository:** Development will continue in the new SvelteKit-based repository.
    
-   **Mobile App:** Enhancements to the Flutter-based mobile app [MicroPyramid/flutter-crm](https://github.com/MicroPyramid/flutter-crm) will depend on increased user engagement or support from a paying client.
    

### Future Vision

This project is far from dead, it’s evolving. I’m committed to its growth and open to discussions about its direction, contributions, or potential collaborations. Feel free to reach out with ideas or feedback.

Thank you for your support and understanding.

## Runcode 

 Runcode is online developer workspace. It is cloud based simple, secure and ready to code workspaces, assuring high performance & fully configurable coding environment. With runcode you can run django-crm(API) with one-click.


- Open below link to create django-crm workspace on [RunCode](https://runcode.io/ "RunCode"). It will create django-crm API

    [![RunCode](https://runcode-app-public.s3.amazonaws.com/images/dark_btn.png)](https://runcode.io)

- After running API, Go to Frontend UI [React CRM](https://github.com/MicroPyramid/react-crm "React CRM") project to create new workspace with runcode.

## Docs

Please [Click Here](http://django-crm.readthedocs.io "Click Here") for latest documentation.

## Project Modules
This project contains the following modules:
- Contacts
- Companies
- Leads
- Accounts
- Invoices (todo)
- Cases (todo)
- Opportunity (todo)

## Try for free [here](https://bottlecrm.io/)

## Installation Guide

We recommend ubuntu 20.04. These instructions are verified for ubuntu 20.04.

#### To install system requirements

```
sudo apt update && sudo apt upgrade -y

sudo apt install python-is-python3 xvfb libfontconfig wkhtmltopdf python3-dev python3-pip build-essential libssl-dev libffi-dev python3-venv redis-server redis-tools virtualenv -y
```

#### Install dependencies

##### Optional (based on personal choice)

```
sudo apt update && sudo apt upgrade -y && sudo apt install zsh python3-virtualenv

sh -c "$(wget -O- https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

pip install virtualenvwrapper

echo "source /home/ubuntu/.local/bin/virtualenvwrapper.sh" >> ~/.zshrc
```

If you want to install postgres, follow https://www.postgresql.org/download/
#### To modify postgresql root password

```
sudo -u postgres psql
ALTER USER postgres WITH PASSWORD 'root';
```

#### Create and activate a virtual environment.
if you installed and configured virtualenv wrapper then use the following
``` 
mkvirtualenv <env_name>
workon <env_name>
```
or else
```
virtualenv venv
source venv/bin/activate
```
Install the project's dependency after activating env

```
pip install -r requirements.txt
```

### Env variables

* Then refer to `env.md` for environment variables and keep those in the `.env` file in the current folder as your project is in.


### Docker / docker-compose
in order to use docker, please run the next commands after cloning repo:
```
docker build -t djcrm:1 -f docker/dockerfile .
docker-compose -f docker/docker-compose.yml up
```

**Note**: you must have docker/docker-compose installed on your host. 
### next steps


```
python manage.py migrate
python manage.py runserver
```
- Then open http://localhost:8000/swagger-ui/ in your browser to explore API.

- After running API, Go to Frontend UI [React CRM](https://github.com/MicroPyramid/react-crm "React CRM") project to configure Fronted UI to interact with API.


## Start celery worker in another terminal window

celery -A crm worker --loglevel=INFO

### Useful tools and packages

```
pipdeptree # to see pip dependency tree
black # to format code to meet python coding standards
pip-check -H  # to see upgradable packages
isort # to sort imports in python
```

### Community

**Note: This repository is no longer actively maintained.** For the latest development and community support, please visit our new SvelteKit-based CRM project:

-   **New Project**: [MicroPyramid/opensource-startup-crm](https://github.com/MicroPyramid/opensource-startup-crm)
-   Follow [@micropyramid](<https://twitter.com/micropyramid>) on Twitter
-   For questions about the legacy Django CRM, check [past issues](<https://github.com/MicroPyramid/Django-CRM/issues>)
-   For new feature requests and active development, visit the [new repository](https://github.com/MicroPyramid/opensource-startup-crm)
-   For commercial support [Contact us](https://micropyramid.com/contact-us/)

## Credits

### Contributors

This project exists thanks to all the people who contributed during its active development!

![image](https://opencollective.com/django-crm/contributors.svg?width=890&button=false)

### Legacy Project Notice

This Django CRM repository is now in maintenance mode. While we welcome your feedback and appreciate past contributions, active development has moved to our new SvelteKit-based CRM solution at [MicroPyramid/opensource-startup-crm](https://github.com/MicroPyramid/opensource-startup-crm).

For commercial support [Contact us](https://micropyramid.com/contact-us/)

# Trigger deploy

