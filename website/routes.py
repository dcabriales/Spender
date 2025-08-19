from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_login import login_user, login_required, logout_user
import datetime
from datetime import timedelta
from .models import User, Expenses, Income, Cycle
from . import db
from sqlalchemy import desc, asc

currentDay = datetime.date.today()


routes = Blueprint("routes", __name__)

class UserData:
    def __init__(self, email):
        self.email = email
        self.account = User.query.filter(User.email == email).first()
        self.income = Income.query.filter(Income.user == self.account.id).order_by(Income.date.desc()).first()
        self.expenses = Expenses.query.filter(Expenses.user == self.account.id).filter(Expenses.date_purchased >= self.income.date).all()

    def total_Expenses(self):
        return sum(exp.cost for exp in self.expenses)
    
    def net_Income(self):
        return self.income.amount - self.total_Expenses()

def spendAmount(incomeAvailable, daysLeft):
    return incomeAvailable / daysLeft


def netIncome(income, expenses):
    return income - expenses


def totalExpenses(expenses):
    total = 0
    for expense in expenses:
        total += expense.cost
    return total


def calculateDaysLeft(dateIncome, nextIncomeDate):
    days = nextIncomeDate - dateIncome
    return int(days.days)

def calculateCycleDays(dateIncome, nextIncomeDate):
    days = nextIncomeDate - dateIncome + timedelta(days=1)
    return int(days.days)

def addExpense(name, user_id, cost, date):
    new_expense = Expenses(expense=name, user=user_id, cost=cost, date_purchased=date)
    db.session.add(new_expense)
    db.session.commit()

def map_exp_date(user):
    mapped_expenses =  {}
    first_day = user.income.date
    days = calculateDaysLeft(first_day, currentDay)
    userExpenses = Expenses.query.filter(Expenses.date_purchased==first_day).all()
    total = 0
    for exp in userExpenses:
        total += exp.cost
    mapped_expenses[first_day] = round(total,2)
    for i in range(days): 
        first_day += datetime.timedelta(days=1)
        userExpenses = Expenses.query.filter(Expenses.date_purchased==first_day).all()
        total = 0
        for exp in userExpenses:
            total += exp.cost
        mapped_expenses[first_day] = round(total,2)
    return mapped_expenses 

@routes.route("/", methods=["GET"])
@login_required
def home():
    user = User.query.filter(User.email == session["email"]).first()
    if Income.query.filter(Income.user == user.id).first() == None:
        return redirect(url_for("routes.NewUserIncome"))
    if user.NextIncomeDate == None:
        return redirect(url_for("routes.nextIncomeDate"))
    user = UserData(session["email"])
    """ calculate data for home page """
    all_dates = date_range_list(user.income.date, user.account.NextIncomeDate)
    ogdaysLeft = calculateDaysLeft(user.income.date, user.account.NextIncomeDate)
    original_spend = spendAmount(user.income.amount, ogdaysLeft)
    
    daysLeft = calculateDaysLeft(currentDay, user.account.NextIncomeDate)
    exp_before_today = Expenses.query.filter(Expenses.user==user.account.id).filter(Expenses.date_purchased >= user.income.date).filter(Expenses.date_purchased < currentDay).all()
    today_expenses = totalExpenses(exp_before_today)
    today_income = netIncome(user.income.amount, today_expenses)
    today_spend = round(spendAmount(today_income, daysLeft),2)

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
    chart_expenses = []
    chart_label_days = month_day_fromDate(all_dates)
    chart_dates = date_range_list(user.income.date, currentDay)
    for date in chart_dates:
        date_expenses = Expenses.query.filter(Expenses.user==user.account.id).filter(Expenses.date_purchased == date).all()
        total =0
        for exp in date_expenses:
            total += exp.cost    
        chart_expenses.append(total)
    dailySpend = []
    for date in chart_dates:
        new_expenses = Expenses.query.filter(Expenses.user==user.account.id).filter(Expenses.date_purchased < date).filter(Expenses.date_purchased >= user.income.date).all()
        total = 0
        for exp in new_expenses:
            total += exp.cost 
        dLeft = calculateDaysLeft(date, user.account.NextIncomeDate)
        newIncome = netIncome(user.income.amount, total)
        new_spend = spendAmount(newIncome, dLeft)
        dailySpend.append(new_spend)
    chart_map = {
        "dates": chart_label_days,
        "expenses": chart_expenses,
        "og_spend": [original_spend for day in range(ogdaysLeft)],
        "daily_spend": dailySpend
    }

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
    return render_template("home.html", chart_map=chart_map, expenses_map=map_exp, income_map=income_info_data)


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
    if request.method == "POST":
        data = request.form
        # pDate = data["datePurchased"]
        date_object = datetime.datetime.strptime(data["NextIncomeDateInput"], '%Y-%m-%d').date()
        user.NextIncomeDate = date_object
        db.session.add(user)
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
    

@routes.route("/incomePage", methods = ["GET"])
@login_required
def income_info():
    if "email" in session:
        user = UserData(session["email"])
    nextIncDate = user.account.NextIncomeDate
    total_expense = totalExpenses(user.expenses)
    incomeAvailable = netIncome(user.income.amount, total_expense)
    income_info_data = {
        "inc_available":round(incomeAvailable,2),
        "nid":nextIncDate,
        "income_amount": user.income.amount,
        "inc_date": user.income.date
    }
    return render_template("incomeInfo.html", data=income_info_data)

@routes.route("/deleteExpense/<expense_id>",methods=["POST"])
@login_required
def delete_expense(expense_id):
    expense = Expenses.query.filter_by(eid=expense_id).first()
    db.session.delete(expense)
    db.session.commit()
    return redirect(url_for("routes.expenses_page"))

def date_range_list(start_date, end_date):
    # Return generator for a list datetime.date objects (inclusive) between start_date and end_date (inclusive).
    date_list = []
    curr_date = start_date
    while curr_date <= end_date:
        date_list.append(curr_date)
        curr_date += timedelta(days=1)
    return date_list

def month_day_fromDate(date_list):
    dataset = []
    for full_date in date_list:
        dataset.append(f"{full_date.month}/{full_date.day}")
    return dataset

@routes.route("/spend", methods=["GET"])
@login_required
def spend_page():
    if "email" in session:
        user = UserData(session["email"])
    all_dates = date_range_list(user.income.date, user.account.NextIncomeDate)
    ogdaysLeft = calculateDaysLeft(user.income.date, user.account.NextIncomeDate)
    original_spend = spendAmount(user.income.amount, ogdaysLeft)
    
    daysLeft = calculateDaysLeft(currentDay, user.account.NextIncomeDate)
    exp_before_today = Expenses.query.filter(Expenses.user==user.account.id).filter(Expenses.date_purchased >= user.income.date).filter(Expenses.date_purchased < currentDay).all()
    today_expenses = totalExpenses(exp_before_today)
    today_income = netIncome(user.income.amount, today_expenses)
    today_spend = round(spendAmount(today_income, daysLeft),2)

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
    chart_expenses = []
    chart_label_days = month_day_fromDate(all_dates)
    chart_dates = date_range_list(user.income.date, currentDay)
    for date in chart_dates:
        date_expenses = Expenses.query.filter(Expenses.user==user.account.id).filter(Expenses.date_purchased == date).all()
        total =0
        for exp in date_expenses:
            total += exp.cost    
        chart_expenses.append(total)
    dailySpend = []
    for date in chart_dates:
        new_expenses = Expenses.query.filter(Expenses.user==user.account.id).filter(Expenses.date_purchased < date).filter(Expenses.date_purchased >= user.income.date).all()
        total = 0
        for exp in new_expenses:
            total += exp.cost 
        dLeft = calculateDaysLeft(date, user.account.NextIncomeDate)
        newIncome = netIncome(user.income.amount, total)
        new_spend = spendAmount(newIncome, dLeft)
        dailySpend.append(new_spend)
    chart_map = {
        "dates": chart_label_days,
        "expenses": chart_expenses,
        "og_spend": [original_spend for day in range(ogdaysLeft)],
        "daily_spend": dailySpend
    }
    return render_template("spender.html",chart_map=chart_map, net_spend=net_spend)

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
    original_spend = spendAmount(cycle_income.amount, ogdaysLeft)
    
    dailySpend = []
    for date in all_dates:
        new_expenses = Expenses.query.filter(Expenses.user==user.account.id).filter(Expenses.date_purchased < date).filter(Expenses.date_purchased >= cycle.start_date).all()
        total = 0
        for exp in new_expenses:
            total += exp.cost 
        dLeft = calculateCycleDays(date, cycle.end_date)
        newIncome = netIncome(cycle_income.amount, total)
        print(newIncome, dLeft, date)
        new_spend = spendAmount(newIncome, dLeft)
        dailySpend.append(new_spend)
    chart_map = {
        "dates": chart_label_days,
        "expenses": chart_expenses,
        "og_spend": [original_spend for day in range(ogdaysLeft)],
        "daily_spend": dailySpend
    }
    return render_template("cycle_info.html", chart_map=chart_map)