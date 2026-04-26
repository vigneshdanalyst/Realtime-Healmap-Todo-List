# TaskBoard

TaskBoard is a simple Flask task tracker built as a weekend project. It includes user registration, login, task creation, task status updates, a small dashboard, a yearly activity heatmap, and basic task analytics.

## Features

- Register and log in with your own account
- Create tasks with title, description, priority, assignee, and due date
- Filter tasks by all, pending, completed, and overdue
- Update task status: Pending, In Progress, Completed, or Blocked
- Edit and delete tasks
- Dashboard with completion stats, recent tasks, monthly chart, and activity heatmap
- SQLite by default, with optional `DATABASE_URL` support

## Tech Stack

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Login
- Flask-Bcrypt
- SQLite by default

## Setup

Clone the project:

```bash
git clone https://github.com/vigneshdanalyst/Realtime-Healmap-Todo-List.git

```

Create and activate a virtual environment:

```bash
python -m venv venv
```

On Windows:

```bash
venv\Scripts\activate
```

On macOS/Linux:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the app:

```bash
python app.py
```

Open the app:

```text
http://127.0.0.1:5000
```

## Login and Password

There is no default username or password.

Each user or GitHub forker should create their own account from the **Register** page:

```text
http://127.0.0.1:5000/register
```

Use any email and password you want for your local copy. The password is not stored as plain text. It is hashed with Flask-Bcrypt and saved in your local database.

After registering, log in here:

```text
http://127.0.0.1:5000/login
```

## Database

By default, the app uses a local SQLite database:

```text
instance/heatmap.db
```

This file is generated automatically when the app runs. It is ignored by Git, so every user or forker gets their own local database.

To use another database, set the `DATABASE_URL` environment variable before running the app.

Example:

```bash
set DATABASE_URL=postgresql://username:password@localhost:5432/taskboard_db
python app.py
```

On macOS/Linux:

```bash
export DATABASE_URL=postgresql://username:password@localhost:5432/taskboard_db
python app.py
```

## Environment Variables

Optional variables:

```text
SECRET_KEY=your-secret-key
DATABASE_URL=your-database-url
```

For local testing, the app has a development fallback secret key. For deployment, always set your own `SECRET_KEY`.

## Project Structure

```text
.
|-- app.py
|-- requirements.txt
|-- static/
|   |-- script.js
|   `-- style.css
`-- templates/
    |-- edit_task.html
    |-- index.html
    |-- layout.html
    |-- login.html
    |-- register.html
    `-- tasks.html
```

## Notes

- Do not commit `instance/heatmap.db`; it contains local user/task data.
- Do not hardcode real passwords or production secrets in the repo.
- If you forget your local password, delete `instance/heatmap.db` and register again.
