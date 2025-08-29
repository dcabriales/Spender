from datetime import timedelta
from .models import Expenses, Cycle, Income
from . import db
import datetime


currentDay = datetime.date.today()

# Return generator for a list datetime.date objects (inclusive) between start_date and end_date (inclusive).
def build_list_dates(start_date, end_date):
    date_list = []
    while start_date <= end_date:
        date_list.append(start_date)
        start_date += timedelta(days=1)
    return date_list

# Return list of dates formatted as "M/D" from a list of datetime.date objects.
def chart_date_labels(start_date, end_date):
    date_list = []
    while start_date <= end_date:
        date_list.append(f"{start_date.month}/{start_date.day}")
        start_date += timedelta(days=1)
    return date_list

def calc_days_remaining(start_date, end_date):
        return int((end_date - start_date).days)
def calc_spendability(income, days):
        return income / days
def netIncome(income, expenses):
    return income - expenses

def totalExpenses(expenses):
    total = 0
    for expense in expenses:
        total += expense.cost
    return total

def calculateCycleDays(dateIncome, nextIncomeDate):
    days = nextIncomeDate - dateIncome + timedelta(days=1)
    return int(days.days)

def add_exp_to_db(user_id, form):
    data = form
    expense_name = data["expenseName"]
    cost = data["expenseCost"]
    purchase_date = data["datePurchased"]
    date_object = datetime.datetime.strptime(purchase_date, '%Y-%m-%d').date()
    new_expense = Expenses(expense=expense_name, user=user_id, cost=cost, date_purchased=date_object)
    db.session.add(new_expense)
    db.session.commit()

def add_nid_db_cycle(user, form):
    amount = float(form["incomeAmount"])
    newIncome = Income(amount=amount,date=user.NextIncomeDate, user=user.id)
    prev_nid = user.NextIncomeDate
    new_nid = datetime.datetime.strptime(form["NextIncomeDateInput"], '%Y-%m-%d').date()
    new_Cycle = Cycle(user=user.id, start_date=prev_nid, end_date=new_nid)
    user.NextIncomeDate = new_nid
    db.session.add(user)
    db.session.commit()
    db.session.add(newIncome)
    db.session.commit()
    db.session.add(new_Cycle)
    db.session.commit()
    return

def map_exp_date(user):
    mapped_expenses =  {}
    first_day = user.income.date
    days = calc_days_remaining(first_day, currentDay)
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