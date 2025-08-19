from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_login import login_user, login_required, logout_user
import datetime
from .models import User, Expenses, Income, Cycle
from .classes import UserData, Chart, calc_days_remaining, calc_spendability, netIncome, date_range_list, month_day_fromDate
from .calc_helpers import (
    date_range_list,
    month_day_fromDate,
    calc_days_remaining,
    calc_spendability,
    netIncome,
    totalExpenses,
    addExpense,
    map_exp_date,
    calculateCycleDays,
)
from . import db
from sqlalchemy import desc, asc


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
    user = UserData(session["email"])
    user_Chart = Chart(user.income, user.expenses, user.account)
    """ calculate data for home page """

    daysLeft = calc_days_remaining(currentDay, user.account.NextIncomeDate)
    exp_before_today = Expenses.query.filter(Expenses.user==user.account.id).filter(Expenses.date_purchased >= user.income.date).filter(Expenses.date_purchased < currentDay).all()
    today_expenses = totalExpenses(exp_before_today)
    today_income = netIncome(user.income.amount, today_expenses)
    today_spend = round(calc_spendability(today_income, daysLeft),2)

    exp_today = Expenses.query.filter(Expenses.user==user.account.id).filter(Expenses.date_purchased == currentDay).all()
    spent_today = totalExpenses(exp_today)
    net_spend = round(today_spend - spent_today,2)
    if net_spend > 0:
        net_spend = str(f"+${net_spend}")
    elif net_spend < 0:
        net_spend = str(f"${net_spend}")
    else:
        net_spend = str("$"+net_spend)
    """ chart data """
    map_exp = map_exp_date(user)
    nextIncDate = user.account.NextIncomeDate
    total_expense = totalExpenses(user.expenses)
    incomeAvailable = netIncome(user.income.amount, total_expense)
    income_info_data = {
        "inc_available":round(incomeAvailable,2),
        "nid":nextIncDate,
        "income_amount": user.income.amount,
        "inc_date": user.income.date
    }
    today_income = netIncome(user.income.amount, today_expenses)
    today_spend = round(calc_spendability(today_income, daysLeft),2)
    exp_before_today = Expenses.query.filter(Expenses.user==user.account.id).filter(Expenses.date_purchased >= user.income.date).filter(Expenses.date_purchased < currentDay).all()
    today_expenses = totalExpenses(exp_before_today)
    daysLeft = calc_days_remaining(currentDay, user.account.NextIncomeDate)

    exp_today = Expenses.query.filter(Expenses.user==user.account.id).filter(Expenses.date_purchased == currentDay).all()
    spent_today = totalExpenses(exp_today)
    net_spend = round(today_spend - spent_today,2)
    if net_spend > 0:
        net_spend = str(f"+${net_spend}")
    elif net_spend < 0:
        net_spend = str(f"${net_spend}")
    else:
        net_spend = str("$"+net_spend)
    
    return render_template("home.html", chart_map=user_Chart.chart_map, expenses_map=map_exp, income_map=income_info_data)


@routes.route("/expenses", methods=["GET", "POST"])
@login_required
def expenses_page():
    if "email" in session:
        user = UserData(session["email"])
    if request.method == "POST":
        data = request.form
        expense = data["expenseName"]
        cost = data["expenseCost"]
        pDate = data["datePurchased"]
        date_object = datetime.datetime.strptime(pDate, '%Y-%m-%d').date()
        addExpense(expense, user.account.id, float(cost), date_object)
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
        data = request.form
        expense = data["expenseName"]
        cost = data["expenseCost"]
        pDate = data["datePurchased"]
        date_object = datetime.datetime.strptime(pDate, '%Y-%m-%d').date()
        addExpense(expense, user.account.id, float(cost), date_object)
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
        prev_nid = datetime.datetime.strptime(data["NextIncomeDateInput"], '%Y-%m-%d').date()

    if request.method == "POST":
        data = request.form
        # pDate = data["datePurchased"]
        date_object = datetime.datetime.strptime(data["NextIncomeDateInput"], '%Y-%m-%d').date()
        user.NextIncomeDate = date_object
        db.session.add(user)
        db.session.commit()
        new_Cycle = Cycle(user=user.id, start_date=prev_nid, end_date=date_object)
        db.session.add(new_Cycle)
        db.session.commit()
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
        newIncome = Income(amount=amount,date=user.account.NextIncomeDate, user=user.account.id)
        db.session.add(newIncome)
        db.session.commit()
        return redirect(url_for("routes.nextIncomeDate"))
    elif request.method == "GET":
        return render_template("incomeUpdate.html", income_date=user.account.NextIncomeDate)
   
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

@routes.route("/cycles", methods = ["GET"])
@login_required
def cycles_page():
    if "email" in session:
        user = UserData(session["email"])
    all_cycles = Cycle.query.filter(Cycle.user==user.account.id).filter(Cycle.start_date != user.income.date).order_by(desc(Cycle.start_date)).all()
    return render_template("cycles.html", all_cycles=all_cycles)

@routes.route("/cycle/<cycle_id>", methods=["GET"])
@login_required
def cycle_info(cycle_id):
    if "email" in session:
        user = UserData(session["email"])

    cycle = Cycle.query.filter(Cycle.cid==cycle_id).filter(Cycle.user == user.account.id).first()
    cycle_income = Income.query.filter(Income.date == cycle.start_date).filter(Income.user == user.account.id).first()    
    all_dates = date_range_list(cycle.start_date, cycle.end_date)
    chart_label_days = month_day_fromDate(all_dates)

    chart_expenses = []
    for date in all_dates:
        date_expenses = Expenses.query.filter(Expenses.user==user.account.id).filter(Expenses.date_purchased == date).all()
        total =0
        for exp in date_expenses:
            total += exp.cost    
        chart_expenses.append(total)

    ogdaysLeft = calculateCycleDays(cycle.start_date, cycle.end_date)
    original_spend = calc_spendability(cycle_income.amount, ogdaysLeft)
    
    dailySpend = []
    for date in all_dates:
        new_expenses = Expenses.query.filter(Expenses.user==user.account.id).filter(Expenses.date_purchased < date).filter(Expenses.date_purchased >= cycle.start_date).all()
        total = 0
        for exp in new_expenses:
            total += exp.cost 
        dLeft = calculateCycleDays(date, cycle.end_date)
        newIncome = netIncome(cycle_income.amount, total)
        print(newIncome, dLeft, date)
        new_spend = calc_spendability(newIncome, dLeft)
        dailySpend.append(new_spend)
    chart_map = {
        "dates": chart_label_days,
        "expenses": chart_expenses,
        "og_spend": [original_spend for day in range(ogdaysLeft)],
        "daily_spend": dailySpend
    }
    return render_template("cycle_info.html", chart_map=chart_map)