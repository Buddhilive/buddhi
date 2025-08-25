![Buddhi AI Logo](./public/logos/buddhi-ai-logo-64.png)

# Buddhi AI

Buddhi AI is a user friendly AI agent development framework.

## Project Setup

To set up the project, follow these steps:

### Create .env file

Create a `.env` file in the root directory of the project and add the following environment variables:

```yml
DEBUG=1
DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1]
SECRET_KEY="<your-secret-key>"
DOMAIN = 'localhost:3000'
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

### Creating a Python Virtual Environment

To create a Python virtual environment named `dojo`, run the following command in your terminal:

```shell
python -m venv dojo
```

To activate the environment on Windows, use:

```shell
.\dojo\Scripts\activate
```

On macOS/Linux, use:

```bash
source dojo/bin/activate
```

### Install Dependencies

To install the required dependencies for the project, run the following command:

```shell
pip install -r requirements.txt
```

### Run backend app

To run the Django backend app, first navigate to backend folder:

```shell
cd backend
```

then start the Django app

```shell
py manage.py runserver
```

### Django Database Migrations

To apply any database changes or migrations run following commands:

```shell
py manage.py makemigrations
py manage.py migrate
```

### Create a Super User (Admin)

To create a superuser (admin) account for the Django admin panel, run the following command:

```shell
py manage.py createsuperuser
```
