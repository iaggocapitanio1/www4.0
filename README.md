# xxxxxxxxxxxxxxxx4.0_API
This is an API that communicates with the ORION-LD broker from Fiware. The main goal of this project is to provide a secure and easy way to authenticate and authorize users to access the data stored in the ORION-LD broker.

[![Run in Postman](https://run.pstmn.io/button.svg)](https://app.getpostman.com/run-collection/24363558-8b8acda5-5376-4f7d-a283-730843947710?action=collection%2Ffork&collection-url=entityId%3D24363558-8b8acda5-5376-4f7d-a283-730843947710%26entityType%3Dcollection%26workspaceId%3Dd81c493b-29e6-48e9-96b9-d8149e2661f8)

## Features

- Authentication and authorization of users through JSON Web Token (JWT)
- Support for different roles (admin, worker, customer)
- Support for creating, reading, updating and deleting entities in the ORION-LD broker
- Support for creating, reading, updating and deleting subscriptions in the ORION-LD broker
- Support for querying the ORION-LD broker using the NGSI-v2 query language

## Technology Stack

- Python 3
- Django 
- Django REST framework
- requests
- PyJWT

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

- Python 3
- pip

### Installation

1. Clone the repository
```sh
git clone https://github.com/iaggocapitanio1/xxxxxxxxxxxxxxxx4.0_API.git
```
2. Install the dependencies

```sh
pip install -r requirements.txt
```

3. Create a file in the root of the project called .env and set the following environment variables:

```.env
POSTGRES_DB=xxxxxxxxxxxxxxxx
DATABASE=xxxxxxxxxxxxxxxx
POSTGRES_USER=xxxxxxxxxxxxxxxx
POSTGRES_PASSWORD=xxxxxxxxxxxxxxxx
POSTGRES_HOST=localhost
POSTGRES_PORT=xxxxxxxxxxxxxxxx
SECRET_KEY=xxxxxxxxxxxxxxxx
DEBUG=True
HASHID_FIELD_SALT=xxxxxxxxxxxxxxxx
EMAIL_HOST_USER=ww4wood@gmail.com
EMAIL_HOST_PASSWORD=xxxxxxxxxxxxxxxx
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST=smtp.gmail.com
DEFAULT_FROM_EMAIL=ww4wood@gmail.com
ORION_HOST=http://localhost:1026
SOCIAL_AUTH_FACEBOOK_KEY=xxxxxxxxxxxxxxxx
SOCIAL_AUTH_FACEBOOK_SECRET=xxxxxxxxxxxxxxxx
```
4. Run the migrations

```commandline
python manage.py makemigrations
python manage.py migrate
```

5. Create a superuser
```commandline
python manage.py createsuperuser
```

6. Run Server

```commandline
python manage.py runserver
```

7. The API will be available at http://127.0.0.1:8000/

## Enviroments Variables 
| Variable Name                          | Default Value                     | Description                                                             |
|----------------------------------------|-----------------------------------|-------------------------------------------------------------------------|
| WW4API_PRODUCTION                      | False                             | Indicates whether the API is in production or not                       |
| WW4API_CREATE_AS_ACTIVE                | True                              | Indicates whether a user account should be created as active by default |
| WW4API_SITE_ACTIVATION_DOMAIN_NAME     | activation                        | Domain name for site activation                                         |
| WW4API_SITE_RESET_PASSWORD_DOMAIN_NAME | reset-password                    | Domain name for password reset                                          |
| WW4API_REDIRECT_TO_FRONT               | False                             | Indicates whether a redirect should be made to the front end            |
| WW4API_SECRET_KEY                      | -                                 | Secret key for the API                                                  |
| WW4API_PASSWORD_RESET_TIMEOUT          | 54000                             | Timeout for password reset in seconds                                   |
| WW4API_SESSION_COOKIE_AGE              | 7200                              | Age of session cookie in seconds                                        |
| WW4API_DEBUG                           | True                              | Indicates whether the API is in debug mode                              |
| WW4API_ALLOWED_HOSTS                   | localhost,xxxxxxxxxxxxxxxx4.pt,127.0.0.1  | List of allowed hosts                                                   |
| WW4API_ORION_HOST                      | http://localhost:1026             | Host for the Orion context broker                                       |
| WW4API_SOCIAL_AUTH_FACEBOOK_KEY        | -                                 | Facebook API key for social authentication                              |
| WW4API_SOCIAL_AUTH_FACEBOOK_SECRET     | -                                 | Facebook API secret for social authentication                           |
| WW4API_EMAIL_USE_TLS                   | True                              | Indicates whether to use TLS for email                                  |
| WW4API_EMAIL_HOST                      | smtp.gmail.com                    | Host for email                                                          |
| WW4API_EMAIL_PORT                      | 5432                              | Port for email                                                          |
| WW4API_EMAIL_HOST_USER                 | ww4wood@gmail.com                 | User for email host                                                     |
| WW4API_EMAIL_HOST_PASSWORD             | mwnwuekrexvhzzgr                  | Password for email host                                                 |
| WW4API_DEFAULT_FROM_EMAIL              | ww4wood@gmail.com                 | Default from email  address                                             |
| WW4API_CORS_ALLOW_METHODS              | DELETE,GET,OPTIONS,PATCH,POST,PUT | List of allowed CORS methods                                            |
| WW4API_HASHID_FIELD_SALT               | -                                 | Salt for hashing fields                                                 |
| WW4API_POSTGRES_DB                     | xxxxxxxxxxxxxxxx                          | Name of the PostgreSQL database                                         |
| WW4API_POSTGRES_USER                   | postgres                          | User for PostgreSQL                                                     |
| WW4API_POSTGRES_HOST                   | localhost                         | Host for PostgreSQL                                                     |
| WW4API_POSTGRES_PORT                   | 5432                              | Port for PostgreSQL                                                     |
| WW4API_POSTGRES_PASSWORD               | -                                 | Postgres Password                                                       |
|                                        |                                   |                                                                         |

## Endpoints