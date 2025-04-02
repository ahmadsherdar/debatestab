# DebateTab

A modern Django-based debate tournament management system that helps organizers run efficient debate competitions. Features include tournament creation, team/speaker management, automated debate pairings, result tracking, and comprehensive statistics.

## 🌟 Features

- **Multi-tournament Support**
  - Create and manage multiple tournaments
  - Customize settings for each tournament
  - Set team sizes and scoring parameters

- **Team & Speaker Management**
  - Register teams and speakers
  - Track speaker scores and statistics
  - Manage team affiliations

- **Tournament Operations**
  - Automated debate pairing generation
  - Real-time result recording
  - Speaker score tracking
  - Motion management for each round

- **Statistics & Reports**
  - Tournament standings
  - Speaker rankings
  - Team performance metrics
  - Round-by-round statistics

## 🚀 Quick Start

1. Clone the repository:
```bash
git clone https://github.com/ahmadsherdar/debatestab.git
cd debatestab
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the database:
```bash
python manage.py migrate
```

5. Create an admin account:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

7. Visit http://127.0.0.1:8000/ in your browser

## 💻 Technology Stack

- Python 3.12
- Django 5.0.6
- Bootstrap 5
- PostgreSQL (Production) / SQLite (Development)
- Gunicorn (Production server)

## 🔧 Configuration

The application uses environment variables for configuration in production:

- `DJANGO_SECRET_KEY`: Your Django secret key
- `DJANGO_SETTINGS_MODULE`: Set to 'debateTab.production_settings'
- `DATABASE_URL`: Your database connection string
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts

## 🌐 Deployment

Ready for deployment on platforms like:
- Render
- Railway
- Heroku
- Any Python-compatible hosting

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 