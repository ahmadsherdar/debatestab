# DebateTab

A simple, lightweight debate tabulation system for managing debate tournaments.

## Features

- Create and manage multiple tournaments
- Register teams and speakers
- Generate debate pairings
- Record results and speaker scores
- View tournament standings and statistics

## Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/debateTab.git
cd debateTab
```

2. Create a virtual environment and activate it:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```
pip install -r requirements.txt
```

4. Run migrations:
```
python manage.py migrate
```

5. Create a superuser:
```
python manage.py createsuperuser
```

6. Run the development server:
```
python manage.py runserver
```

7. Access the application at http://127.0.0.1:8000/

## Usage

1. Log in with your superuser account
2. Create a new tournament from the dashboard
3. Add teams to your tournament
4. Create rounds and generate debate pairings
5. Record results and speaker scores
6. View standings and statistics

## Requirements

- Python 3.8+
- Django 5.0+

## License

This project is licensed under the MIT License - see the LICENSE file for details. 