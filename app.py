from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)
from flask_bcrypt import Bcrypt
from datetime import datetime,date

app = Flask(__name__)

# Secret key (required for login sessions)
app.config["SECRET_KEY"] = "supersecretkey"

# PostgreSQL connection
app.config["SQLALCHEMY_DATABASE_URI"] = \
"postgresql://postgres:dataengineer2026@localhost:5432/heatmap_db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ----------------------------
# USER TABLE
# ----------------------------

class User(UserMixin, db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ----------------------------
# HEATMAP TABLE
# ----------------------------

class Heatmap(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )

    day_index = db.Column(
        db.Integer
    )

    value = db.Column(
        db.Integer,
        default=0
    )
class Task(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text
    )

    status = db.Column(
        db.String(50),
        default="Pending"
    )

    priority = db.Column(
        db.String(50),
        default="Medium"
    )

    due_date = db.Column(
        db.Date,
        nullable=True
    )

    created_by = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )

    assigned_to = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
def update_heatmap_for_today(user_id, status_type):

    today = date.today()

    start_of_year = date(today.year, 1, 1)

    day_index = (today - start_of_year).days

    record = Heatmap.query.filter_by(
        user_id=user_id,
        day_index=day_index
    ).first()

    if record:

        record.value = status_type

    else:

        record = Heatmap(
            user_id=user_id,
            day_index=day_index,
            value=status_type
        )

        db.session.add(record)

    db.session.commit()
def check_overdue_tasks(user_id):

    today = date.today()

    overdue_tasks = Task.query.filter(
        Task.created_by == user_id,
        Task.due_date < today,
        Task.status != "Completed"
    ).all()

    if overdue_tasks:

        update_heatmap_for_today(
            user_id,
            3   # Red
        )

# ----------------------------
# NOTIFICATION TABLE
# ----------------------------

class Notification(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )

    message = db.Column(
        db.String(255)
    )

    is_read = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
# ----------------------------
# ROUTES
# ----------------------------

@app.route("/")
@login_required
def home():

    # Check overdue tasks
    check_overdue_tasks(current_user.id)

    total_tasks = Task.query.filter_by(
        created_by=current_user.id
    ).count()

    completed_tasks = Task.query.filter_by(
        created_by=current_user.id,
        status="Completed"
    ).count()

    pending_tasks = Task.query.filter_by(
        created_by=current_user.id,
        status="Pending"
    ).count()

    inprogress_tasks = Task.query.filter_by(
        created_by=current_user.id,
        status="In Progress"
    ).count()

    if total_tasks > 0:

        completion_rate = round(
            (completed_tasks / total_tasks) * 100,
            2
        )

    else:

        completion_rate = 0

    return render_template(
        "index.html",
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        inprogress_tasks=inprogress_tasks,
        completion_rate=completion_rate
    )


# ----------------------------
# REGISTER
# ----------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = bcrypt.generate_password_hash(
            password
        ).decode("utf-8")

        user = User(
            username=username,
            email=email,
            password=hashed_password
        )

        db.session.add(user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")


# ----------------------------
# LOGIN
# ----------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(
            email=email
        ).first()

        if user and bcrypt.check_password_hash(
            user.password,
            password
        ):

            login_user(user)

            return redirect(url_for("home"))

    return render_template("login.html")


# ----------------------------
# LOGOUT
# ----------------------------

@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(url_for("login"))

# ----------------------------
# VIEW TASKS
# ----------------------------
@app.route("/tasks")
@login_required
def tasks():

    filter_type = request.args.get("filter")

    users = User.query.all()

    today = date.today()

    # Default → show all user tasks

    query = Task.query.filter(
        (Task.created_by == current_user.id) |
        (Task.assigned_to == current_user.id)
    )

    if filter_type == "my":

        query = query.filter(
            Task.created_by == current_user.id
        )

    elif filter_type == "assigned":

        query = query.filter(
            Task.assigned_to == current_user.id
        )

    elif filter_type == "completed":

        query = query.filter(
            Task.status == "Completed"
        )

    elif filter_type == "pending":

        query = query.filter(
            Task.status == "Pending"
        )

    elif filter_type == "overdue":

        query = query.filter(
            Task.due_date < today,
            Task.status != "Completed"
        )

    all_tasks = query.all()

    return render_template(
        "tasks.html",
        tasks=all_tasks,
        users=users,
        current_date=today
    )
# ----------------------------
# CREATE TASK
# ----------------------------
@app.route("/create_task", methods=["POST"])
@login_required
def create_task():

    title = request.form["title"]

    description = request.form["description"]

    priority = request.form["priority"]

    assigned_to = request.form["assigned_to"]

    due_date = request.form["due_date"]

    # Convert string to date

    if due_date:
        due_date = datetime.strptime(
            due_date,
            "%Y-%m-%d"
        ).date()
    else:
        due_date = None

    task = Task(

        title=title,

        description=description,

        priority=priority,

        assigned_to=assigned_to,

        created_by=current_user.id,

        due_date=due_date

    )

    db.session.add(task)

    db.session.commit()

    return redirect(url_for("tasks"))
# ----------------------------
# UPDATE TASK STATUS
# ----------------------------
@app.route("/update_status/<int:task_id>", methods=["POST"])
@login_required
def update_status(task_id):

    task = Task.query.get(task_id)

    if task:

        new_status = request.form["status"]

        # Completed → Green
        if new_status == "Completed":

            update_heatmap_for_today(
                current_user.id,
                1
            )

        # In Progress → Blue
        elif new_status == "In Progress":

            update_heatmap_for_today(
                current_user.id,
                2
            )

        # Blocked → Purple
        elif new_status == "Blocked":

            update_heatmap_for_today(
                current_user.id,
                5
            )

        task.status = new_status

        db.session.commit()

    return redirect(url_for("tasks"))
# ----------------------------
# DELETE TASK
# ----------------------------

@app.route("/delete_task/<int:task_id>")
@login_required
def delete_task(task_id):

    task = Task.query.get(task_id)

    if task:

        db.session.delete(task)

        db.session.commit()

    return redirect(url_for("tasks"))
# ----------------------------
# EDIT TASK
# ----------------------------

@app.route("/edit_task/<int:task_id>", methods=["GET", "POST"])
@login_required
def edit_task(task_id):

    task = Task.query.get(task_id)

    users = User.query.all()

    if request.method == "POST":

        task.title = request.form["title"]

        task.description = request.form["description"]

        task.priority = request.form["priority"]

        task.assigned_to = request.form["assigned_to"]

        db.session.commit()

        return redirect(url_for("tasks"))

    return render_template(
        "edit_task.html",
        task=task,
        users=users
    )
# ----------------------------
# LOAD HEATMAP DATA
# ----------------------------

@app.route("/data")
@login_required
def get_data():

    records = Heatmap.query.filter_by(
        user_id=current_user.id
    ).all()

    result = {}

    for r in records:
        result[r.day_index] = r.value

    return jsonify(result)


# ----------------------------
# UPDATE HEATMAP
# ----------------------------

@app.route("/update", methods=["POST"])
@login_required
def update_heatmap():

    data = request.json

    day = data.get("day")
    value = data.get("value")

    record = Heatmap.query.filter_by(
        user_id=current_user.id,
        day_index=day
    ).first()

    if record:
        record.value = value
    else:
        record = Heatmap(
            user_id=current_user.id,
            day_index=day,
            value=value
        )
        db.session.add(record)

    db.session.commit()

    return jsonify({"status": "success"})

@app.route("/chart-data")
@login_required
def chart_data():

    tasks = Task.query.filter_by(
        created_by=current_user.id,
        status="Completed"
    ).all()

    date_counts = {}

    for task in tasks:

        if task.created_at:

            day = task.created_at.strftime("%Y-%m-%d")

            if day in date_counts:
                date_counts[day] += 1
            else:
                date_counts[day] = 1

    labels = list(date_counts.keys())

    values = list(date_counts.values())

    return jsonify({
        "labels": labels,
        "values": values
    })

# ----------------------------
# RUN APP
# ----------------------------

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(debug=True)