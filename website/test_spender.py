import pytest
from website import create_app, db
from website.models import User, Income

user_test_data = {
    'email': 'test@example.com',
    'password': 'password123'
}
expired_income_test_data = {
    'incomeAmount': 1000,
    'incomeDate': '2025-01-01',
}

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
        test_user = User.query.filter(User.email == user_test_data["email"]).first()
        if test_user:
            # Delete all incomes for this user first
                Income.query.filter(Income.user == test_user.id).delete()
                db.session.delete(test_user)
                db.session.commit()

@pytest.fixture
def cycle_client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            test_user = User(email=user_test_data["email"], name="Test User", password=user_test_data["password"])
            db.session.add(test_user)
            db.session.commit()
            test_user_income = Income(amount=1000,
                                      date=expired_income_test_data['incomeDate'],
                                      user=test_user.id)
            db.session.add(test_user_income)
            db.session.commit()
        yield client
        with app.app_context():
            test_user = User.query.filter(User.email == user_test_data["email"]).first()
            if test_user:
                Income.query.filter(Income.user == test_user.id).delete()
                db.session.delete(test_user)
                db.session.commit()


def test_create_new_user(client):
    response = client.post('/signup', data=user_test_data)
    assert response.status_code == 302  # Redirect after registration

def test_login_current_user(client):
    # First, create user
    client.post('/signup', data=user_test_data)
    # Then, login
    response = client.post('/login', data=user_test_data)
    assert response.status_code == 302  # Redirect after login

def test_login_expired_cycle_user(cycle_client):
    # Create user and set expired cycle in DB as needed

    response = cycle_client.post('/login', data=user_test_data, follow_redirects=True)
    # Check for expired cycle handling (e.g., redirect, message)
    redirects = []
    while response.status_code in (301, 302, 303, 307, 308):
        location = response.headers.get('Location')
        print(f"Redirect to: {location}")
        redirects.append(location)
        response = client.get(location, follow_redirects=False)
    next_url = response.headers.get('Location')
    response = cycle_client.get(next_url)
    print(response.headers.get('Location'))  # Debug output to see the response content
    assert b'Cycle expired' in response.data or response.status_code == 302

def test_access_without_login(client):
    response = client.get('/expenses')
    assert response.status_code == 302  # Should redirect to login
