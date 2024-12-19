from flask import Blueprint, render_template, request, redirect, url_for, session
import datetime
from datetime import timedelta
from .models import User, Expenses, Income, Cycle
from . import db
from sqlalchemy import desc, asc

currentDay = datetime.date.today()


routes = Blueprint("routes", __name__)


def spendAmount(incomeAvailable, daysLeft):
    return incomeAvailable / daysLeft


def calculateIncome(income, expenses):
    return income - expenses


def calculateExpenses(expenses):
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

def gather_user_data(username):
    user_acc = User.query.filter_by(name=username).first()
    userInc = Income.query.filter(Income.user==user_acc.id).order_by(Income.date.desc()).first()
    userExpenses = Expenses.query.filter(Expenses.user==user_acc.id).filter(Expenses.date_purchased >= userInc.date).all()
    return {"account": user_acc, "income":userInc,"expenses":userExpenses}

def map_exp_date(user):
    mapped_expenses =  {}
    user["expenses"]
    first_day = user["income"].date
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
def home():
    user_data =  gather_user_data("Cabriales")
    if user_data["account"].NextIncomeDate <= datetime.date.today():
        return redirect(url_for("routes.updateIncomePage"))
    all_dates = date_range_list(user_data["income"].date, user_data["account"].NextIncomeDate)
    ogdaysLeft = calculateDaysLeft(user_data["income"].date, user_data["account"].NextIncomeDate)
    original_spend = spendAmount(user_data["income"].amount, ogdaysLeft)
    
    daysLeft = calculateDaysLeft(currentDay, user_data["account"].NextIncomeDate)
    exp_before_today = Expenses.query.filter(Expenses.user==user_data["account"].id).filter(Expenses.date_purchased >= user_data["income"].date).filter(Expenses.date_purchased < currentDay).all()
    today_expenses = calculateExpenses(exp_before_today)
    today_income = calculateIncome(user_data["income"].amount, today_expenses)
    today_spend = round(spendAmount(today_income, daysLeft),2)

    exp_today = Expenses.query.filter(Expenses.user==user_data["account"].id).filter(Expenses.date_purchased == currentDay).all()
    spent_today = calculateExpenses(exp_today)
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
    chart_dates = date_range_list(user_data["income"].date, currentDay)
    for date in chart_dates:
        date_expenses = Expenses.query.filter(Expenses.user==user_data["account"].id).filter(Expenses.date_purchased == date).all()
        total =0
        for exp in date_expenses:
            total += exp.cost    
        chart_expenses.append(total)
    dailySpend = []
    for date in chart_dates:
        new_expenses = Expenses.query.filter(Expenses.user==user_data["account"].id).filter(Expenses.date_purchased < date).filter(Expenses.date_purchased >= user_data["income"].date).all()
        total = 0
        for exp in new_expenses:
            total += exp.cost 
        dLeft = calculateDaysLeft(date, user_data["account"].NextIncomeDate)
        newIncome = calculateIncome(user_data["income"].amount, total)
        new_spend = spendAmount(newIncome, dLeft)
        dailySpend.append(new_spend)
    chart_map = {
        "dates": chart_label_days,
        "expenses": chart_expenses,
        "og_spend": [original_spend for day in range(ogdaysLeft)],
        "daily_spend": dailySpend
    }

    map_exp = map_exp_date(user_data)

    nextIncDate = user_data["account"].NextIncomeDate
    total_expense = calculateExpenses(user_data["expenses"])
    incomeAvailable = calculateIncome(user_data["income"].amount, total_expense)
    income_info_data = {
        "inc_available":round(incomeAvailable,2),
        "nid":nextIncDate,
        "income_amount": user_data["income"].amount,
        "inc_date": user_data["income"].date
    }
    return render_template("home.html", chart_map=chart_map, expenses_map=map_exp, income_map=income_info_data)


@routes.route("/expenses", methods=["GET", "POST"])
def expenses_page():
    user_data =  gather_user_data("Cabriales")
    if request.method == "POST":
        data = request.form
        expense = data["expenseName"]
        cost = data["costInput"]
        pDate = data["purchaseDate"]
        date_object = datetime.datetime.strptime(pDate, '%Y-%m-%d').date()
        addExpense(expense, user_data["account"].id, float(cost), date_object)
        return redirect("expenses")
    elif request.method == "GET":
        total_expense = calculateExpenses(user_data["expenses"])
        map_exp = map_exp_date(user_data)
        return render_template("expenses.html", expensesList = user_data["expenses"], total_exp=total_expense, expenses_map=map_exp)

@routes.route("/fillexpenses", methods=["GET", "POST"])
def fillexpenses():
    if request.method == "POST":
        user_data =  gather_user_data("Cabriales")
        data = request.form
        expense = data["expenseName"]
        cost = data["costInput"]
        pDate = data["purchaseDate"]
        date_object = datetime.datetime.strptime(pDate, '%Y-%m-%d').date()
        addExpense(expense, user_data["account"].id, float(cost), date_object)
        return redirect(url_for("routes.fillexpenses"))
    elif request.method == "GET":
        total_expense = calculateExpenses(user_data["expenses"])
        return render_template("remainingExpenses.html", expensesList = user_data["expenses"], total_exp=total_expense)


@routes.route("/NextIncomeDate", methods =["GET","POST"])
def nextIncomeDate():
    if request.method == "POST":
        user_data =  gather_user_data("Cabriales")
        user_acc = User.query.filter_by(name=user_data["account"].name).first()
        data = request.form
        pDate = data["purchaseDate"]
        date_object = datetime.datetime.strptime(pDate, '%Y-%m-%d').date()
        user_acc.NextIncomeDate = date_object
        db.session.commit()
        return redirect(url_for("routes.fillexpenses"))
    elif request.method == "GET":
        return render_template("NextIncomeUpdate.html", NID=user_data["account"].NextIncomeDate)
   
@routes.route("/UpdateIncome", methods =["GET","POST"])
def updateIncomePage():
    user_data =  gather_user_data("Cabriales")
    if request.method == "POST":
        data = request.form
        amount = float(data["incomeAmount"])
        newIncome = Income(amount=amount,date=user_data["account"].NextIncomeDate, user=user_data["account"].id)
        db.session.add(newIncome)
        db.session.commit()
        return redirect(url_for("routes.nextIncomeDate"))
    elif request.method == "GET":
        return render_template("incomeUpdate.html", income_date=user_data["account"].NextIncomeDate)
   
@routes.route("/incomePage", methods = ["GET"])
def income_info():
    user_data =  gather_user_data("Cabriales")
    nextIncDate = user_data["account"].NextIncomeDate
    total_expense = calculateExpenses(user_data["expenses"])
    incomeAvailable = calculateIncome(user_data["income"].amount, total_expense)
    income_info_data = {
        "inc_available":round(incomeAvailable,2),
        "nid":nextIncDate,
        "income_amount": user_data["income"].amount,
        "inc_date": user_data["income"].date
    }
    return render_template("incomeInfo.html", data=income_info_data)

@routes.route("/deleteExpense/<expense_id>",methods=["POST"])
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
def spend_page():
    user_data =  gather_user_data("Cabriales")
    all_dates = date_range_list(user_data["income"].date, user_data["account"].NextIncomeDate)
    ogdaysLeft = calculateDaysLeft(user_data["income"].date, user_data["account"].NextIncomeDate)
    original_spend = spendAmount(user_data["income"].amount, ogdaysLeft)
    
    daysLeft = calculateDaysLeft(currentDay, user_data["account"].NextIncomeDate)
    exp_before_today = Expenses.query.filter(Expenses.user==user_data["account"].id).filter(Expenses.date_purchased >= user_data["income"].date).filter(Expenses.date_purchased < currentDay).all()
    today_expenses = calculateExpenses(exp_before_today)
    today_income = calculateIncome(user_data["income"].amount, today_expenses)
    today_spend = round(spendAmount(today_income, daysLeft),2)

    exp_today = Expenses.query.filter(Expenses.user==user_data["account"].id).filter(Expenses.date_purchased == currentDay).all()
    spent_today = calculateExpenses(exp_today)
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
    chart_dates = date_range_list(user_data["income"].date, currentDay)
    for date in chart_dates:
        date_expenses = Expenses.query.filter(Expenses.user==user_data["account"].id).filter(Expenses.date_purchased == date).all()
        total =0
        for exp in date_expenses:
            total += exp.cost    
        chart_expenses.append(total)
    dailySpend = []
    for date in chart_dates:
        new_expenses = Expenses.query.filter(Expenses.user==user_data["account"].id).filter(Expenses.date_purchased < date).filter(Expenses.date_purchased >= user_data["income"].date).all()
        total = 0
        for exp in new_expenses:
            total += exp.cost 
        dLeft = calculateDaysLeft(date, user_data["account"].NextIncomeDate)
        newIncome = calculateIncome(user_data["income"].amount, total)
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
def cycles_page():
    user_data =  gather_user_data("Cabriales")
    all_cycles = Cycle.query.filter(Cycle.user==user_data["account"].id).filter(Cycle.start_date != user_data["income"].date).order_by(desc(Cycle.start_date)).all()
    return render_template("cycles.html", all_cycles=all_cycles)

@routes.route("/cycle/<cycle_id>", methods=["GET"])
def cycle_info(cycle_id):
    user_data =  gather_user_data("Cabriales")
    cycle = Cycle.query.filter(Cycle.cid==cycle_id).filter(Cycle.user == user_data["account"].id).first()
    cycle_income = Income.query.filter(Income.date == cycle.start_date).filter(Income.user == user_data["account"].id).first()    
    all_dates = date_range_list(cycle.start_date, cycle.end_date)
    chart_label_days = month_day_fromDate(all_dates)

    chart_expenses = []
    for date in all_dates:
        date_expenses = Expenses.query.filter(Expenses.user==user_data["account"].id).filter(Expenses.date_purchased == date).all()
        total =0
        for exp in date_expenses:
            total += exp.cost    
        chart_expenses.append(total)

    ogdaysLeft = calculateCycleDays(cycle.start_date, cycle.end_date)
    original_spend = spendAmount(cycle_income.amount, ogdaysLeft)
    
    dailySpend = []
    for date in all_dates:
        new_expenses = Expenses.query.filter(Expenses.user==user_data["account"].id).filter(Expenses.date_purchased < date).filter(Expenses.date_purchased >= cycle.start_date).all()
        total = 0
        for exp in new_expenses:
            total += exp.cost 
        dLeft = calculateCycleDays(date, cycle.end_date)
        newIncome = calculateIncome(cycle_income.amount, total)
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

@routes.route("/Signup", methods = ["GET"])
def sign():
    return render_template("signin.html")