# JobPoint Surigao - Job Portal System

A comprehensive job portal system built with Django, designed specifically for the Surigao region. This platform connects job seekers with employers, providing a seamless experience for both parties.

## Features

### For Job Seekers
- User registration and profile management
- Job search with advanced filters
- Job application tracking
- Resume upload and management
- Real-time notifications
- Location-based job search
- Personalized job recommendations
- Application status tracking
- Profile visibility settings

### For Employers
- Company profile management
- Job posting and management
- Applicant tracking
- Application review system
- Analytics dashboard
- Email notifications
- Job posting analytics
- Candidate shortlisting
- Bulk application processing

### General Features
- Responsive design with mobile optimization
- Real-time updates
- Secure file handling
- Location hierarchy (Country > Province > City > Barangay)
- Advanced search functionality
- User authentication and authorization
- Admin dashboard
- Profile picture management
- Interactive UI elements
- Dark/Light mode support
- Multi-language support

## Technical Stack

- **Backend**: Django 5.2
- **Database**: PostgreSQL
- **Cache**: Redis
- **Frontend**: 
  - HTML5, CSS3, JavaScript
  - Bootstrap 5
  - Font Awesome Icons
  - Custom CSS animations
- **Real-time**: Django Channels
- **Task Queue**: Celery
- **Search**: Django Filter
- **Forms**: Crispy Forms
- **API**: Django REST Framework
- **Authentication**: Django Allauth
- **File Storage**: AWS S3 (optional)

## Prerequisites

- Python 3.11+
- PostgreSQL 12+
- Redis 6+
- Node.js 14+ (for frontend assets)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/jobpoint-surigao.git
cd jobpoint-surigao
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and configure your environment variables:
```env
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

DB_NAME=jobportal
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

REDIS_URL=redis://localhost:6379

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@jobportal.com

# Optional: AWS S3 Configuration
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=your-region
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Collect static files:
```bash
python manage.py collectstatic
```

8. Run the development server:
```bash
python manage.py runserver
```

## Development

### Running Tests
```bash
python manage.py test
```

### Code Style
The project follows PEP 8 guidelines. Use the following tools to maintain code quality:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run linting
flake8

# Run type checking
mypy .

# Run tests with coverage
coverage run manage.py test
coverage report
```

### Database Migrations
When making changes to models:

```bash
python manage.py makemigrations
python manage.py migrate
```

## Deployment

### Production Settings
1. Set `DEBUG=False` in `.env`
2. Configure proper `ALLOWED_HOSTS`
3. Set up SSL certificates
4. Configure proper database credentials
5. Set up Redis for caching and channels
6. Configure email settings
7. Set up AWS S3 for file storage (optional)
8. Configure proper security headers
9. Set up monitoring and logging

### Using Docker
1. Build the Docker image:
```bash
docker build -t jobpoint-surigao .
```

2. Run the container:
```bash
docker run -d -p 8000:8000 jobpoint-surigao
```

## Project Structure

```
jobpoint-surigao/
├── jobportal/              # Project settings
├── jobs/                   # Main application
│   ├── migrations/        # Database migrations
│   ├── templates/         # HTML templates
│   ├── static/           # Static files
│   ├── tests/            # Test files
│   ├── models.py         # Database models
│   ├── views.py          # View logic
│   ├── forms.py          # Form definitions
│   └── urls.py           # URL routing
├── static/                # Project-wide static files
├── templates/             # Project-wide templates
├── media/                 # User-uploaded files
├── requirements.txt       # Python dependencies
├── requirements-dev.txt   # Development dependencies
└── manage.py             # Django management script
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, email support@jobpoint-surigao.com or join our Slack channel.

## Acknowledgments

- Django community
- Bootstrap team
- All contributors and supporters 