from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, DateField, SelectField, PasswordField, EmailField
from wtforms.validators import DataRequired, email

class RegisterForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Sign Up")


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class AddTask(FlaskForm):
    task_name = StringField('Task Name', validators=[DataRequired()])
    task_description = TextAreaField('Description', validators=[DataRequired()])
    due_date = DateField('Due Date', validators=[DataRequired()])
    progress = SelectField('Progress', choices=[('Not Started'), ('In Progress'), ('Completed')], validators=[DataRequired()])
    add_task = SubmitField('Submit')


