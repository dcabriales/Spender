# SpenderApp
Flask app

Spender is a web service meant to improve people's spending and budgeting habits.
It is a budgeting app that formulates a number that represents the optimal amount of expenses a user should limit themselves to on that day. This app uses user variables such as the amount of income, pay cycle dates, expenses, and other related data points to calculate the "Spend" amount.

It is important to visualize the data points and analyze it in a way that helps the user become more financially aware.

Features
- View previous cycles
- Chart representing essential data points

Future 
- Implement a tag system for each expense
- Log in system
- Add Income during a cycle

To deploy web service
run:
py app.py

work on refactoring user class functions

docker run --rm -v c:\Users\dcabr\Documents\postgresqldb-vol:/var/lib/postgresql/data -e POSTGRES_PASSWORD=mypassword -e POSTGRES_HOST_AUTH_METHOD=trust -p 5432:5432 90da0743e4ed

command to run db