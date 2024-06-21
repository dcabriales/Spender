from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
import datetime

db = SQLAlchemy()
DB_NAME = "database.db"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'ASDFJKL ASDFJKL'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    from .routes import routes

    app.register_blueprint(routes, url_prefix='/')

    from .models import User, Expenses, Income, Cycle
   
    with app.app_context():
        # oldd = Cycle(start_date=datetime.date(2024,5,31),end_date=datetime.date(2024,6,13),user=1)
        # new = Cycle(start_date=datetime.date(2024,6,14),end_date=datetime.date(2024,6,27),user=1)
        db.create_all()

    return app
