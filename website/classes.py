from .models import User, Expenses, Income, Cycle
from .calc_helpers import (
    build_list_dates,
    calculateCycleDays,
    chart_date_labels,
    calc_days_remaining,
    calc_spendability,
    netIncome,
)
import datetime


currentDay = datetime.date.today()

class UserData:
    def __init__(self, email):
        self.email = email
        self.user = User.query.filter(User.email == email).first()
        self.income = Income.query.filter(Income.user == self.user.id).order_by(Income.date.desc()).first()
        self.expenses = Expenses.query.filter(Expenses.user == self.user.id).filter(Expenses.date_purchased >= self.income.date).all()

class Chart(UserData):
    def __init__(self, email):
        super().__init__(email)
        self.start_date = self.income.date
        self.end_date = self.user.NextIncomeDate
        self.income_amount = self.income.amount
        self.chart_date_labels = chart_date_labels(self.start_date, self.end_date)
        self.chart_map_values = self.chart_calc_data()

    def chart_page_details(self):
        chart_details = {
            "dates": self.chart_date_labels,
            "expenses": self.daily_total_exp_list,
            "og_spend": self.og_spendability,
            "daily_spend": self.spendability_perdate_list
        }
        return chart_details

    def chart_calc_data(self):
        # Original spendability calculation
        og_days = calc_days_remaining(self.start_date, self.end_date)
        og_spendability = calc_spendability(self.income_amount, og_days)
        # Income Date to Current Day calculations
        dates_until_today = build_list_dates(self.start_date, currentDay)
        daily_total_exp_list = []
        spendability_perdate_list = []
        for date in dates_until_today:
            date_expenses = Expenses.query.filter(Expenses.user==self.user.id).filter(Expenses.date_purchased == date).all()
            total =0
            for exp in date_expenses:
                total += exp.cost
            daily_total_exp_list.append(total)
            days_until_nid = calc_days_remaining(date, self.end_date)
            net_income_ondate = netIncome(self.income_amount, total)
            spendability_perdate = calc_spendability(net_income_ondate, days_until_nid)
            spendability_perdate_list.append(spendability_perdate)
        self.daily_total_exp_list = daily_total_exp_list
        self.spendability_perdate_list = spendability_perdate_list
        self.og_spendability = [og_spendability for day in range(og_days)]

class CycleClass(Chart):
    def __init__(self, email, cycle_id):
        super().__init__(email)
        self.cycle = Cycle.query.filter(Cycle.cid==cycle_id).filter(Cycle.user == self.user.id).first()
        self.cycle_start_date = self.cycle.start_date
        self.cycle_end_date = self.cycle.end_date
        self.cycle_income = Income.query.filter(Income.date == self.cycle.start_date).filter(Income.user == self.user.id).first().amount

    def cycle_map(self):
        chart_label_days = chart_date_labels(self.cycle_start_date, self.cycle_end_date)
        all_dates = build_list_dates(self.cycle_start_date, self.cycle_end_date)
        chart_expenses = []
        for date in all_dates:
            date_expenses = Expenses.query.filter(Expenses.user==self.user.id).filter(Expenses.date_purchased == date).all()
            total =0
            for exp in date_expenses:
                total += exp.cost    
            chart_expenses.append(total)

        ogdaysLeft = calculateCycleDays(self.cycle_start_date, self.cycle_end_date)
        original_spend = calc_spendability(self.cycle_income, ogdaysLeft)
        
        dailySpend = []
        for date in all_dates:
            new_expenses = Expenses.query.filter(Expenses.user==self.user.id).filter(Expenses.date_purchased < date).filter(Expenses.date_purchased >= self.cycle_start_date).all()
            total = 0
            for exp in new_expenses:
                total += exp.cost 
            dLeft = calculateCycleDays(date, self.cycle_end_date)
            newIncome = netIncome(self.cycle_income, total)
            new_spend = calc_spendability(newIncome, dLeft)
            dailySpend.append(new_spend)
        chart_map = {
            "dates": chart_label_days,
            "expenses": chart_expenses,
            "og_spend": [original_spend for day in range(ogdaysLeft)],
            "daily_spend": dailySpend
        }
        return chart_map
