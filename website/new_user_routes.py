from flask import Blueprint, render_template, request, redirect, url_for, session
from datetime import datetime
from .models import User, Income
from . import db

new_user = Blueprint("new_user", __name__)

@new_user.route("/Income_Input", methods = ["GET","POST"])
def NewUserIncome():
    if "email" in session:
        userEmail = session["email"]
        user = User.query.filter_by(email=userEmail).first()
    if request.method == "POST":
        data = request.form
        amount = float(data["incomeAmount"])
        date = datetime.datetime.strptime(data["incomeDate"], '%Y-%m-%d').date()
        newIncome = Income(amount=amount,date=date, user=user.id)
        db.session.add(newIncome)
        db.session.commit()
        return redirect(url_for("routes.home"))
    elif request.method == "GET":
        return render_template("newUserIncome.html")