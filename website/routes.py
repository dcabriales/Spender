from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_login import login_user, login_required, logout_user
import datetime
from .models import Expenses
from .classes import UserData, CycleClass
from .calc_helpers import (
    netIncome,
    totalExpenses,
    add_exp_to_db,
    map_exp_date,
    add_nid_db_cycle
)
from . import db


currentDay = datetime.date.today()

routes = Blueprint("routes", __name__)

@routes.route("/", methods=["GET"])
@login_required
def home():
    user = CycleClass(session["email"])
    print(user)
    """ Check if Cycle has ended  """
    if user.current_cycle.end_date <= currentDay:
        return redirect(url_for("routes.new_cycle"))

    map_exp = map_exp_date(user)
    total_expense = totalExpenses(user.expenses)
    incomeAvailable = netIncome(user.income.amount, total_expense)
    income_info_data = {
        "inc_available":round(incomeAvailable,2),
        "nid":user.current_cycle.end_date,
        "income_amount": user.income.amount,
        "inc_date": user.income.date
    }

    return render_template("home.html", chart_map=user.cycle_map(), expenses_map=map_exp, income_map=income_info_data, cycles=user.all_cycles)

@routes.route("/expenses", methods=["GET", "POST"])
@login_required
def expenses_page():
    if "email" in session:
        user = UserData(session["email"])
    if request.method == "POST":
        add_exp_to_db(user.user.id, request.form)
        return redirect("expenses")
    elif request.method == "GET":
        total_expense = totalExpenses(user.expenses)
        map_exp = map_exp_date(user)
        return render_template("expenses.html", expensesList = user.expenses, total_exp=total_expense, expenses_map=map_exp)
# feature needs to be added
@routes.route("/deleteExpense/<expense_id>",methods=["POST"])
@login_required
def delete_expense(expense_id):
    expense = Expenses.query.filter_by(eid=expense_id).first()
    db.session.delete(expense)
    db.session.commit()
    return redirect(url_for("routes.expenses_page"))

@routes.route("/cycle/<cycle_id>", methods=["GET"])
@login_required
def cycle_info(cycle_id):
    if "email" in session:
        user_cycle = CycleClass(session["email"], cycle_id)
    return render_template("cycle_info.html", chart_map=user_cycle.cycle_map())

@routes.route("/new_cycle", methods=["GET","POST"])
@login_required
def new_cycle():
    if "email" in session:
        user = UserData(session["email"])
    if request.method == "POST":
        if request.form.get("form_type") == "expense":
            add_exp_to_db(user.user.id, request.form)
            return redirect(url_for("routes.new_cycle"))
        if request.form.get("form_type") == "income":
            add_nid_db_cycle(user.user, request.form)
            return redirect(url_for("routes.new_cycle"))
        else:
            return redirect(url_for("routes.home"))
    if request.method == "GET":
        return render_template("new_cycle.html")
