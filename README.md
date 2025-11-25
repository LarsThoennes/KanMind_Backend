## KanMind Backend

**KanMind Backend** is the server-side application for a task management platform that allows users to register, create boards, and manage tasks.  
Each task can include comments, and both boards and tasks support roles such as *creator* and *member*.

---

## Technologies
- **Python**
- **Django**
- **Django REST Framework**

---

## Features
- User registration and authentication  
- Board creation and management  
- Task creation within boards  
- Commenting on tasks  
- Role-based access control for creators and members (boards & tasks)

---

Installation

## 1. Clone the repository
```bash
git clone <repository-url>
cd <repository-folder>

```
## Create a virtual environment
```bash
python -m venv venv
```
## Activate the environment

## macOS/Linux
```bash
source venv/bin/activate
```
## Windows
```bash
venv\Scripts\activate
```
## Install dependencies
```bash
pip install -r requirements.txt
```

## Create migrations
```bash
python manage.py makemigrations
```
## Apply migrations
```bash
python manage.py migrate
```
## Optional) Create a superuser for the admin panel
```bash
python manage.py createsuperuser
```
## Run the Development Server
```bash
python manage.py runserver
```
## The server will start at:
```bash
http://127.0.0.1:8000/
```
