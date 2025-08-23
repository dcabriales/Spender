from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_login import login_user, login_required, logout_user
import datetime
from .models import User, Expenses, Income, Cycle
from .classes import UserData, Chart, CycleClass, calc_days_remaining, calc_spendability, netIncome
from .calc_helpers import (
    calc_days_remaining,
    calc_spendability,
    netIncome,
    totalExpenses,
    add_exp_to_db,
    map_exp_date,
    add_nid_db_cycle,  # Added import for add_nid_db_cycle
)
from . import db
from sqlalchemy import desc


currentDay = datetime.date.today()

routes = Blueprint("routes", __name__)

@routes.route("/", methods=["GET"])
@login_required
def home():
    user = User.query.filter(User.email == session["email"]).first()
    if Income.query.filter(Income.user == user.id).first() == None:
        return redirect(url_for("routes.NewUserIncome"))
    if user.NextIncomeDate == None:
        return redirect(url_for("routes.nextIncomeDate"))
    user_Chart = Chart(session["email"])

    """ calculate data for home page """
    daysLeft = calc_days_remaining(currentDay, user_Chart.user.NextIncomeDate)
    exp_before_today = Expenses.query.filter(Expenses.user==user_Chart.user.id).filter(Expenses.date_purchased >= user_Chart.income.date).filter(Expenses.date_purchased < currentDay).all()
    today_expenses = totalExpenses(exp_before_today)
    today_income = netIncome(user_Chart.income.amount, today_expenses)
    today_spend = round(calc_spendability(today_income, daysLeft),2)

    exp_today = Expenses.query.filter(Expenses.user==user_Chart.user.id).filter(Expenses.date_purchased == currentDay).all()
    spent_today = totalExpenses(exp_today)
    net_spend = round(today_spend - spent_today,2)
    if net_spend > 0:
        net_spend = str(f"+${net_spend}")
    elif net_spend < 0:
        net_spend = str(f"${net_spend}")
    else:
        net_spend = str("$"+net_spend)
    """ chart data """
    map_exp = map_exp_date(user_Chart)
    nextIncDate = user_Chart.user.NextIncomeDate
    total_expense = totalExpenses(user_Chart.expenses)
    incomeAvailable = netIncome(user_Chart.income.amount, total_expense)
    income_info_data = {
        "inc_available":round(incomeAvailable,2),
        "nid":nextIncDate,
        "income_amount": user_Chart.income.amount,
        "inc_date": user_Chart.income.date
    }
    today_income = netIncome(user_Chart.income.amount, today_expenses)
    today_spend = round(calc_spendability(today_income, daysLeft),2)
    exp_before_today = Expenses.query.filter(Expenses.user==user_Chart.user.id).filter(Expenses.date_purchased >= user_Chart.income.date).filter(Expenses.date_purchased < currentDay).all()
    today_expenses = totalExpenses(exp_before_today)
    daysLeft = calc_days_remaining(currentDay, user_Chart.user.NextIncomeDate)

    exp_today = Expenses.query.filter(Expenses.user==user_Chart.user.id).filter(Expenses.date_purchased == currentDay).all()
    spent_today = totalExpenses(exp_today)
    net_spend = round(today_spend - spent_today,2)
    if net_spend > 0:
        net_spend = str(f"+${net_spend}")
    elif net_spend < 0:
        net_spend = str(f"${net_spend}")
    else:
        net_spend = str("$"+net_spend)
    all_cycles = Cycle.query.filter(Cycle.user == user_Chart.user.id).filter(Cycle.start_date != user_Chart.income.date).order_by(desc(Cycle.start_date)).all()

    return render_template("home.html", chart_map=user_Chart.chart_page_details(), expenses_map=map_exp, income_map=income_info_data, cycles=all_cycles)

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

@routes.route("/fillexpenses", methods=["GET", "POST"])
@login_required
def fillexpenses():
    if "email" in session:
        user = UserData(session["email"])
    if request.method == "POST":
        add_exp_to_db(user.user.id, request.form)
        return redirect(url_for("routes.fillexpenses"))
    elif request.method == "GET":
        total_expense = totalExpenses(user.expenses)
        return render_template("remainingExpenses.html", expensesList = user.expenses, total_exp=total_expense)


@routes.route("/NextIncomeDate", methods =["GET","POST"])
@login_required
def nextIncomeDate():
    NID=None
    print("In next income date page")
    if "email" in session:
        user = User.query.filter(User.email == session["email"]).first()
    if request.method == "POST":
        add_nid_db_cycle(request.form, user.id)
        return redirect(url_for("routes.home"))
    elif request.method == "GET":
        return render_template("NextIncomeUpdate.html", NID=NID)
   
@routes.route("/UpdateIncome", methods =["GET","POST"])
@login_required
def updateIncomePage():
    if "email" in session:
        user = UserData(session["email"])
    if request.method == "POST":
        print("form submitted")
        data = request.form
        amount = float(data["incomeAmount"])
        newIncome = Income(amount=amount,date=user.user.NextIncomeDate, user=user.user.id)
        db.session.add(newIncome)
        db.session.commit()
        return redirect(url_for("routes.nextIncomeDate"))
    elif request.method == "GET":
        return render_template("incomeUpdate.html", income_date=user.user.NextIncomeDate)
   
@routes.route("/NewUserIncome", methods = ["GET","POST"])
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