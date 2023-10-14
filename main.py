import sqlalchemy.exc
import sqlalchemy.orm.exc
from flask import Flask, render_template, redirect, request, url_for, flash, get_flashed_messages
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, LoginManager, current_user, UserMixin, logout_user
from forms import RegisterForm, LoginForm, AddTask
import os
import calendar

#https://github.com/SortableJS/Sortable/tree/master/plugins

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
Bootstrap5(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
db = SQLAlchemy()
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))


class TaskDB(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    task_name = db.Column(db.String(250), nullable=False, unique=True)
    task_description = db.Column(db.String(250), nullable=False)
    due_date = db.Column(db.Date())
    progress = db.Column(db.String(20))

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


with app.app_context():
    db.create_all()


@app.route("/", methods=["GET", "POST"])
def home():

    if current_user.is_authenticated:

        not_started = db.session.execute(db.select(TaskDB).where(
            (TaskDB.user_id == current_user.id) & (TaskDB.progress == 'Not Started')).order_by(TaskDB.due_date)).scalars()

        in_progress = db.session.execute(db.select(TaskDB).where(
                (TaskDB.user_id == current_user.id) & (TaskDB.progress == 'In Progress')).order_by(TaskDB.due_date)).scalars()

        completed = db.session.execute(db.select(TaskDB).where(
                (TaskDB.user_id == current_user.id) & (TaskDB.progress == 'Completed')).order_by(TaskDB.due_date)).scalars()


        return render_template("index.html", not_started=not_started, in_progress=in_progress, completed=completed)

    else:
        return render_template("index.html")



@app.route("/add/<progress>", methods=["GET", "POST"])
def add(progress):

    form = AddTask(progress=progress)
    data = form.data

    if form.validate_on_submit():
        try:
            with app.app_context():
                new_task = TaskDB(task_name=data['task_name'],
                                  task_description=data['task_description'],
                                  due_date=data['due_date'],
                                  progress=data['progress'],
                                  user_id=current_user.id)
                db.session.add(new_task)
                db.session.commit()

            return redirect(url_for('home'))

        except sqlalchemy.exc.IntegrityError:
            flash('Task name is taken, please select another task name.')
            return render_template("add.html", form=form)
        except sqlalchemy.orm.exc.DetachedInstanceError:
            db.session.expire_all()
            #db.session.refresh()
            return redirect(url_for('home'))
    else:
        return render_template('add.html', form=form)



@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):

    with app.app_context():
        task = db.session.execute(db.select(TaskDB).where(TaskDB.id == id)).scalar()
    form = AddTask(obj=task)

    if form.validate_on_submit():

        try:
            with app.app_context():
                data = form.data
                task = db.session.execute(db.select(TaskDB).where(TaskDB.id == id)).scalar()
                task.task_name = data['task_name']
                task.task_description = data['task_description']
                task.due_date = data['due_date']
                task.progress = data['progress']
                task.user_id = current_user.id
                db.session.commit()
            return redirect(url_for('home'))

        except sqlalchemy.exc.IntegrityError:
            flash('Task name is taken, please select another task name.')
            return render_template("edit.html", task=task, form=form)

        except sqlalchemy.orm.exc.DetachedInstanceError:
            db.session.expire_all()
            #db.session.refresh()
            return redirect(url_for('home'))
    else:
        return render_template("edit.html", task=task, form=form)


@app.route("/delete/<int:id>")
def delete(id):
    with app.app_context():
        task_delete = db.session.execute(db.select(TaskDB).where(TaskDB.id == id)).scalar()
        db.session.delete(task_delete)
        db.session.commit()
    return redirect('/')

@app.route("/details/<int:id>")
def details(id):

    with app.app_context():
        task_details = db.session.execute(db.select(TaskDB).where(TaskDB.id == id)).scalar()

    return render_template("details.html", task=task_details)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()

        if not user:
            flash("That email does not exist, please try again.")
            return render_template('login.html', form=form, current_user=current_user)

        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return render_template('login.html', form=form, current_user=current_user)
        else:
            login_user(user)
            return redirect(url_for('home'))
    else:

        return render_template("login.html", form=form, current_user=current_user)

@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if user:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for("home"))
    return render_template("register.html", form=form, current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))





if __name__ == '__main__':
    app.run(debug=True)
