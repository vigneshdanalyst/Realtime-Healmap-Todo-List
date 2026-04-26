import os
from datetime import datetime, date

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

app = Flask(__name__)

# Security & Database Configuration
os.makedirs(app.instance_path, exist_ok=True)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///heatmap.db")
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
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_app_name():
    return {"app_name": "TaskBoard"}

# ----------------------------
# TASK TABLE
# ----------------------------

class Task(db.Model):
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default="Pending")
    priority = db.Column(db.String(50), default="Medium")
    due_date = db.Column(db.Date, nullable=True)
    
    # Collaboration
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    assigned_to = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    creator = db.relationship("User", foreign_keys=[created_by], backref="tasks_created")
    assignee = db.relationship("User", foreign_keys=[assigned_to], backref="tasks_assigned")

# ----------------------------
# HEATMAP TABLE
# ----------------------------

class Heatmap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    day_index = db.Column(db.Integer)
    value = db.Column(db.Integer, default=0)

# ----------------------------
# LOGIC HELPERS
# ----------------------------

def update_heatmap_for_today(user_id, status_type):
    today = date.today()
    start_of_year = date(today.year, 1, 1)
    day_index = (today - start_of_year).days

    record = Heatmap.query.filter_by(user_id=user_id, day_index=day_index).first()

    if record:
        # Intensity increment for completions (Max 4)
        if status_type == 1:
            record.value = min(record.value + 1, 4)
        else:
            record.value = status_type
    else:
        record = Heatmap(user_id=user_id, day_index=day_index, value=status_type)
        db.session.add(record)
    
    db.session.commit()

def can_access_task(task):
    return task and (task.created_by == current_user.id or task.assigned_to == current_user.id)

def parse_due_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date() if value else None

def status_to_heatmap_value(status):
    return {
        "Pending": 0,
        "In Progress": 2,
        "Completed": 1,
        "Blocked": 5,
    }.get(status, 0)

# ----------------------------
# CORE ROUTES
# ----------------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not username or not email or not password:
            return render_template("register.html", error="All fields are required."), 400

        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            return render_template("register.html", error="Username or email already exists."), 409

        user = User(
            username=username,
            email=email,
            password=bcrypt.generate_password_hash(password).decode("utf-8")
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("home"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("home"))

        return render_template("login.html", error="Invalid email or password."), 401

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def home():
    # Dashboard Analytics
    visible_tasks = Task.query.filter((Task.created_by == current_user.id) | (Task.assigned_to == current_user.id))
    total_tasks = visible_tasks.count()
    completed = visible_tasks.filter(Task.status == "Completed").count()
    pending = visible_tasks.filter(Task.status == "Pending").count()
    in_progress = visible_tasks.filter(Task.status == "In Progress").count()
    overdue = visible_tasks.filter(Task.due_date < date.today(), Task.status != "Completed").count()
    recent_tasks = visible_tasks.order_by(Task.created_at.desc()).limit(5).all()
    
    rate = round((completed / total_tasks) * 100, 2) if total_tasks > 0 else 0

    return render_template("index.html", 
                           total_tasks=total_tasks, 
                           completed_tasks=completed, 
                           pending_tasks=pending, 
                           in_progress_tasks=in_progress,
                           overdue_tasks=overdue,
                           recent_tasks=recent_tasks,
                           completion_rate=rate)

@app.route("/tasks")
@login_required
def tasks():
    filter_type = request.args.get("filter")
    users = User.query.all()
    today = date.today()

    query = Task.query.filter((Task.created_by == current_user.id) | (Task.assigned_to == current_user.id))

    if filter_type == "completed":
        query = query.filter(Task.status == "Completed")
    elif filter_type == "pending":
        query = query.filter(Task.status == "Pending")
    elif filter_type == "overdue":
        query = query.filter(Task.due_date < today, Task.status != "Completed")

    return render_template("tasks.html", tasks=query.order_by(Task.created_at.desc()).all(), users=users, active_filter=filter_type or "all")

@app.route("/create_task", methods=["POST"])
@login_required
def create_task():
    due = request.form.get("due_date")
    due_date = parse_due_date(due)
    assigned_to = request.form.get("assigned_to") or current_user.id
    
    task = Task(
        title=request.form.get("title", "").strip(),
        description=request.form.get("description", "").strip(),
        priority=request.form.get("priority", "Medium"),
        assigned_to=int(assigned_to),
        created_by=current_user.id,
        due_date=due_date
    )
    db.session.add(task)
    db.session.commit()
    return redirect(url_for("tasks"))

@app.route("/edit_task/<int:task_id>", methods=["GET", "POST"])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    users = User.query.all()

    # Only the creator or the assigned user can edit.
    if not can_access_task(task):
        return redirect(url_for("tasks"))

    if request.method == "POST":
        task.title = request.form.get("title", "").strip()
        task.description = request.form.get("description", "").strip()
        task.priority = request.form.get("priority", "Medium")
        task.assigned_to = int(request.form.get("assigned_to") or current_user.id)
        
        due = request.form.get("due_date")
        task.due_date = parse_due_date(due)

        db.session.commit()
        return redirect(url_for("tasks"))

    return render_template("edit_task.html", task=task, users=users)

@app.route("/delete_task/<int:task_id>")
@login_required
def delete_task(task_id):
    task = Task.query.get(task_id)
    # Only allow the creator to delete.
    if task and task.created_by == current_user.id:
        db.session.delete(task)
        db.session.commit()
    return redirect(url_for("tasks"))

@app.route("/update_status/<int:task_id>", methods=["POST"])
@login_required
def update_status(task_id):
    task = Task.query.get_or_404(task_id)
    if not can_access_task(task):
        return redirect(url_for("tasks"))

    status = request.form.get("status", "Pending")
    allowed_statuses = {"Pending", "In Progress", "Completed", "Blocked"}
    if status in allowed_statuses:
        task.status = status
        db.session.commit()
        update_heatmap_for_today(current_user.id, status_to_heatmap_value(status))

    return redirect(url_for("tasks"))

@app.route("/data")
@login_required
def get_data():
    records = Heatmap.query.filter_by(user_id=current_user.id).all()
    return jsonify({r.day_index: r.value for r in records})

@app.route("/chart-data")
@login_required
def chart_data():
    labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    values = [0] * 12
    tasks = Task.query.filter((Task.created_by == current_user.id) | (Task.assigned_to == current_user.id)).all()

    for task in tasks:
        month_index = task.created_at.month - 1
        values[month_index] += 1

    return jsonify({"labels": labels, "values": values})

# ----------------------------
# RUN ENGINE
# ----------------------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
