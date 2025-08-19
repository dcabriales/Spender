from .models import User, Expenses, Income
from .calc_helpers import (
    date_range_list,
    month_day_fromDate,
    calc_days_remaining,
    calc_spendability,
    netIncome,
)
import datetime


currentDay = datetime.date.today()

class UserData:
    def __init__(self, email):
        self.email = email
        self.account = User.query.filter(User.email == email).first()
        self.income = Income.query.filter(Income.user == self.account.id).order_by(Income.date.desc()).first()
        self.expenses = Expenses.query.filter(Expenses.user == self.account.id).filter(Expenses.date_purchased >= self.income.date).all()

class BudgetCalculator:
    def __init__(self, income, expenses, next_income_date):
        self.income = income
        self.expenses = expenses
        self.next_income_date = next_income_date

    def expenses_sum(self):
        return sum(exp.cost for exp in self.expenses)

    def net_income(self):
        return self.income.amount - self.expenses_sum()

    def days_between_incomes(self):
        return calc_days_remaining(self.income.date, self.next_income_date)

    def original_spendability_number(self):
        return calc_spendability(self.net_income(), self.days_between_incomes())

class Chart:
    def __init__(self, income, expenses, user):
        self.income = income
        self.expenses = expenses
        self.user = user

        self.chart_map = self.chart_map_values()

    def chart_map_values(self):
        og_days = calc_days_remaining(self.income.date, self.user.NextIncomeDate)
        og_spendability = calc_spendability(self.income.amount, og_days)
        all_dates = date_range_list(self.income.date, self.user.NextIncomeDate)
        chart_label_days = month_day_fromDate(all_dates)
        chart_dates = date_range_list(self.income.date, currentDay)
        chart_expenses = []
        dailySpend = []
        for date in chart_dates:
            date_expenses = Expenses.query.filter(Expenses.user==self.user.id).filter(Expenses.date_purchased == date).all()
            total =0
            for exp in date_expenses:
                total += exp.cost    
            chart_expenses.append(total)
            dLeft = calc_days_remaining(date, self.user.NextIncomeDate)
            newIncome = netIncome(self.income.amount, total)
            new_spend = calc_spendability(newIncome, dLeft)
            dailySpend.append(new_spend)
        chart_map = {
            "dates": chart_label_days,
            "expenses": chart_expenses,
            "og_spend": [og_spendability for day in range(og_days)],
            "daily_spend": dailySpend
        }
        return chart_map
    
