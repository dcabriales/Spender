from datetime import timedelta
from .models import Expenses
from . import db
import datetime


currentDay = datetime.date.today()

""" Chart functions """
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
def month_day_fromDate(date_list):
    dataset = []
    for full_date in date_list:
        dataset.append(f"{full_date.month}/{full_date.day}")
    return dataset



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

def addExpense(name, user_id, cost, date):
    new_expense = Expenses(expense=name, user=user_id, cost=cost, date_purchased=date)
    db.session.add(new_expense)
    db.session.commit()

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