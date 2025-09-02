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
from sqlalchemy import desc


currentDay = datetime.date.today()

class UserData:
    def __init__(self, email):
        self.email = email
        self.user = User.query.filter(User.email == email).first()
        self.income = Income.query.filter(Income.user == self.user.id).order_by(Income.date.desc()).first()
        self.expenses = Expenses.query.filter(Expenses.user == self.user.id).filter(Expenses.date_purchased >= self.income.date).all()
        self.current_cycle = Cycle.query.filter(Cycle.user == self.user.id).order_by(Cycle.end_date.desc()).first()

    def __str__(self):
        return f"'{self.email}' - User ID: {self.user.id} - Income: {self.income.amount} on {self.income.date} - Current Cycle: {self.current_cycle.start_date} to {self.current_cycle.end_date}"

class CycleClass(UserData):
    def __init__(self, email, cycle_id=None):
        super().__init__(email)
        self.all_cycles = Cycle.query.filter(Cycle.user == self.user.id).filter(Cycle.start_date != self.income.date).order_by(desc(Cycle.start_date)).all()
        if cycle_id != self.current_cycle.cid and cycle_id is not None:
            self.cycle = Cycle.query.filter(Cycle.cid==cycle_id).filter(Cycle.user == self.user.id).first()
            self.cycle_start_date = self.cycle.start_date
            self.cycle_end_date = self.cycle.end_date
            self.cycle_income = Income.query.filter(Income.date == self.cycle.start_date).filter(Income.user == self.user.id).first().amount
        else:
            self.cycle = Cycle.query.filter(Cycle.user == self.user.id).order_by(Cycle.end_date.desc()).first()
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
        if self.current_cycle.cid == self.cycle.cid:
            # Income Date to Current Day calculations
            dates_until_today = build_list_dates(self.cycle.start_date, currentDay)
            daily_total_exp_list = []
            for date in dates_until_today:
                date_expenses = Expenses.query.filter(Expenses.user==self.user.id).filter(Expenses.date_purchased == date).all()
                total =0
                for exp in date_expenses:
                    total += exp.cost
                daily_total_exp_list.append(total)
                days_until_nid = calc_days_remaining(date, self.cycle.end_date)
                net_income_ondate = netIncome(self.income.amount, total)
                spendability_perdate = calc_spendability(net_income_ondate, days_until_nid)
                dailySpend.append(spendability_perdate)
        else:
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
