from . import db
from flask_login import UserMixin
import datetime


class User(db.Model):
    # __tablename__ = "user_account"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    NextIncomeDate = db.Column(db.Date)


    def __init__(self, name, NextIncomeDate):
        self.name = name
        self.NextIncomeDate = NextIncomeDate


    def __repr__(self):
        return f"User(id={self.id}, name={self.name}, NextIncomeDate={self.NextIncomeDate})"


class Expenses(db.Model):
    # __tablename__ = "user_expenses"
    eid = db.Column(db.Integer, primary_key=True)
    expense = db.Column(db.String(30))
    user = db.Column(db.Integer, db.ForeignKey("user.id"))
    cost = db.Column(db.Float)
    date_purchased = db.Column(db.Date, default=datetime.date.today())


    def __init__(self, expense, user, cost, date_purchased):
        self.expense = expense
        self.user = user
        self.cost = cost
        self.date_purchased = date_purchased


    def __repr__(self):
        return f"Expenses(id={self.eid}, expense={self.expense}, name={self.user}, cost={self.cost}, date_purchased={self.date_purchased})"
   
class Income(db.Model):
    # __tablename__ = "user_income"
    iid = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float)
    date = db.Column(db.Date)
    user = db.Column(db.Integer, db.ForeignKey("user.id"))


    def __init__(self, amount, date, user):
        self.amount = amount
        self.date = date
        self.user = user


    def __repr__(self):
        return f"Income(id={self.iid}, amount={self.amount}, date={self.date}, user={self.user})"

class Cycle(db.Model):
    cid = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey("user.id"))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)

    def __init__(self,user,start_date,end_date):
        self.user = user
        self.start_date = start_date
        self.end_date = end_date

    def __repr__(self):
        return f"Cycle(user={self.user}, start_date={self.start_date}, end_date={self.end_date})"