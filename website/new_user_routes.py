from flask import Blueprint, render_template, request, redirect, url_for, session
import datetime
from .models import User, Income, Cycle
from . import db

new_user = Blueprint("new_user", __name__)

@new_user.route("/Income_Input", methods = ["GET","POST"])
def new_details():
    if "email" in session:
        userEmail = session["email"]
        user = User.query.filter_by(email=userEmail).first()
    if request.method == "POST":
        data = request.form
        amount = float(data["incomeAmount"])
        income_date = datetime.datetime.strptime(data["incomeDate"], '%Y-%m-%d').date()
        nid = data["NextIncomeDateInput"]
        newIncome = Income(amount=amount,date=income_date, user=user.id)
        db.session.add(newIncome)
        db.session.commit()
        new_Cycle = Cycle(user=user.id, start_date=income_date, end_date=nid)
        db.session.add(new_Cycle)
        db.session.commit()
        return redirect(url_for("auth.login"))
    elif request.method == "GET":
        return render_template("new_user.html")