from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from os import path
import datetime
from flask_migrate import Migrate

db = SQLAlchemy()
DB_NAME = "database.db"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'ASDFJKL ASDFJKL'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://postgres:mypassword@localhost:5432/spender-flaskDB'
    db.init_app(app)
    migrate = Migrate(app, db)
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from .routes import routes
    from .auth import auth as auth_blueprint

    app.register_blueprint(routes, url_prefix='/')
    app.register_blueprint(auth_blueprint)

    from .models import User, Expenses, Income, Cycle
    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return User.query.get(int(user_id))
    with app.app_context():
        db.session.commit()
        db.create_all()

    return app
