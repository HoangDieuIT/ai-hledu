# Hexagon Education API

A comprehensive FastAPI backend system for educational platform management with automated email notifications, course management, student enrollment, and content delivery.

## Features

- **Course Management**: Complete course and class management system
- **Student Enrollment**: Automated enrollment with class code and online forms
- **Email Notifications**: Automated email system for inquiries and enrollments
- **News & Content**: News management with categories and filtering
- **File Management**: Secure file upload/download with access controls
- **Contact System**: Contact inquiry management with admin notifications
- **User Authentication**: Firebase-based authentication system
- **Storage Integration**: Support for S3, MinIO, and local storage
- **Admin Integration**: Synchronized with Django admin panel
- **API Documentation**: Interactive Swagger/OpenAPI documentation

## Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Email System](#email-system)
- [Database Setup](#database-setup)
- [Development](#development)
- [Deployment](#deployment)
- [Contributing](#contributing)

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL
- Redis (optional, for caching)
- Gmail account (for email notifications)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd hexagon-backend/HexagonApi
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment setup**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Run the application**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

The API will be available at `http://localhost:8001`

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Application
NAME=Hexagon Education API
VERSION=1.0.0
ENV=dev

# Database
DB__DSN=postgresql+asyncpg://user:password@localhost/hexagon_db
DB__POOL_SIZE=20
DB__ECHO=false

# Storage (choose one)
STORAGE__URL=local://app/static/uploads
# STORAGE__URL=s3://your-bucket?region=us-east-1
# STORAGE__URL=minio://localhost:9000/your-bucket

# Firebase Authentication
FIREBASE__PROJECT_ID=your-project-id
FIREBASE__PRIVATE_KEY_ID=your-private-key-id
FIREBASE__PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE__CLIENT_EMAIL=firebase-adminsdk-xxx@your-project.iam.gserviceaccount.com
FIREBASE__CLIENT_ID=your-client-id
FIREBASE__AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE__TOKEN_URI=https://oauth2.googleapis.com/token

# Email Configuration
EMAIL__HOST=smtp.gmail.com
EMAIL__PORT=587
EMAIL__USERNAME=your-email@domain.com
EMAIL__PASSWORD=your-app-password
EMAIL__FROM_EMAIL=your-email@domain.com
EMAIL__FROM_NAME=Hexagon Education
EMAIL__TEMPLATE_DIR=app/templates/email
EMAIL__STATIC_DIR=app/static/email

# Timezone
TZ__TIMEZONE=Asia/Ho_Chi_Minh

# Documentation
DOCS_USERNAME=admin
DOCS_PASSWORD=admin123
```

### Email Setup

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
   - Use this password in `EMAIL__PASSWORD`

3. **Configure Admin Email** in Django Admin:
   - Add site setting: `admin_notification_email`
   - Value: admin email address for notifications

## API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/register` | User registration | No |
| POST | `/api/auth/login` | User login | No |
| POST | `/api/auth/refresh` | Refresh token | Yes |
| GET | `/api/auth/profile` | Get user profile | Yes |
| PUT | `/api/auth/profile` | Update user profile | Yes |

### Course Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/courses` | List courses with pagination | No |
| GET | `/api/courses/{course_id}` | Get course details | No |
| GET | `/api/courses/slug/{slug}` | Get course by slug | No |
| GET | `/api/courses/{course_id}/classes` | List course classes | No |
| GET | `/api/courses/categories` | List course categories | No |

### Enrollment Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/enrollment/my-enrollments` | Get user enrollments | Yes |
| POST | `/api/enrollment/enroll-by-class-code` | Enroll using class code | Yes |
| POST | `/api/enrollment/submit-online-enrollment` | Submit online enrollment | Yes |
| GET | `/api/enrollment/{enrollment_id}` | Get enrollment details | Yes |

### News Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/news` | List news with pagination | No |
| GET | `/api/news/{news_id}` | Get news details | No |
| GET | `/api/news/slug/{slug}` | Get news by slug | No |
| GET | `/api/news/categories` | List news categories | No |

### Contact Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/contact/course-inquiry` | Submit course inquiry | No |

### File Management Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/files/{file_id}/download` | Download course file | Yes |
| GET | `/api/files/{file_id}/info` | Get file information | Yes |

### Website Configuration Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/website/config` | Get website configuration | No |
| GET | `/api/website/homepage` | Get homepage data | No |
| GET | `/api/website/contact-info` | Get contact information | No |

### Admin Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/admin/dashboard` | Admin dashboard data | Yes (Admin) |
| GET | `/api/admin/enrollments` | All enrollments (admin) | Yes (Admin) |
| PUT | `/api/admin/enrollments/{id}` | Update enrollment | Yes (Admin) |

## Email System

The system automatically sends emails for:

### Contact Inquiries
- **Admin Notification**: Sent to configured admin email
- **Customer Confirmation**: Sent to customer's email (if provided)

### Course Enrollments
- **Admin Notification**: New enrollment alert for admin
- **Welcome Email**: Welcome message for new students

### Email Templates

Located in `app/templates/email/`:
- `contact_inquiry_admin.html` - Admin notification for new inquiries
- `contact_inquiry_customer.html` - Customer confirmation email
- `enrollment_admin.html` - Admin notification for new enrollments
- `enrollment_welcome.html` - Student welcome email

### Email Flow

```
User Action → Service Layer → Email Service → Gmail SMTP → Email Delivery
     ↓              ↓             ↓              ↓            ↓
Contact Form → contact.py → email.py → GmailEmailService → Admin + Customer
Enrollment   → enrollment.py    ↓         Templates        Student + Admin
```

## Database Setup

### Django Admin Integration

The system uses Django admin for content management:

1. **Install Django dependencies**
2. **Run migrations** in Django project
3. **Create superuser** for admin access
4. **Configure site settings** in Django admin

### Database Models

- **Users**: User accounts and profiles
- **Courses**: Course information and categories
- **Classes**: Course class schedules and details
- **Enrollments**: Student enrollments and payments
- **News**: News articles and categories
- **Contact**: Contact inquiries and responses
- **Files**: Course materials and downloads
- **Settings**: Site configuration and settings

## Development

### Project Structure

```
HexagonApi/
├── app/
│   ├── api/              # API routes and endpoints
│   ├── ext/              # Extensions (email, storage, firebase)
│   ├── model/            # Database models and composites
│   ├── service/          # Business logic services
│   ├── templates/        # Email templates
│   ├── static/           # Static files
│   ├── config.py         # Configuration management
│   ├── main.py           # FastAPI application
│   └── resources.py      # Resource management
├── requirements.txt      # Python dependencies
├── .env.example         # Environment template
├── EMAIL_SETUP.md       # Email setup guide
└── README.md           # This file
```

### Running Development Server

```bash
pip install -r requirements.txt

uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

ENV=dev uvicorn app.main:app --reload
```

### API Documentation

- **Swagger UI**: `http://localhost:8001/docs`
- **ReDoc**: `http://localhost:8001/redoc`
- **OpenAPI JSON**: `http://localhost:8001/openapi.json`

### Testing

```bash
curl -X POST "http://localhost:8001/api/contact/course-inquiry" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "test",
    "phone": "0912345678",
    "email": "test@gmail.com",
    "message": "I want to learn more about your courses"
  }'

curl "http://localhost:8001/api/courses?page=1&per_page=10"
```

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Configuration

For production deployment:

1. **Set environment variables**
2. **Configure database connection**
3. **Set up SSL certificates**
4. **Configure reverse proxy** (Nginx/Apache)
5. **Set up monitoring** and logging

### Production Checklist

- Environment variables configured
- Database migrations applied
- Static files properly served
- SSL certificates installed
- Email configuration tested
- Storage system configured
- Backup strategy implemented
- Logging set up

## Features Overview

### Core Capabilities

- **25+ API Endpoints** with comprehensive functionality
- **Automated Email System** with beautiful HTML templates
- **File Upload/Download** with access control
- **Pagination & Filtering** on all list endpoints
- **Permission System** with role-based access
- **Multi-storage Support** (S3, MinIO, Local)
- **Firebase Authentication** integration
- **Django Admin Integration** for content management
- **Interactive API Documentation** with Swagger UI
- **Error Handling** with meaningful error messages

### Email Notifications

- **Contact Inquiry Notifications**
- **Enrollment Confirmations**
- **Admin Alerts**
- **HTML Email Templates**
- **Automated Delivery**

### API Response Format

All API responses follow a consistent format:

```json
{
  "items": ["..."],      // For list endpoints
  "total": 100,        // Total count for pagination
  "page": 1,           // Current page
  "perPage": 20,       // Items per page
  "totalPages": 5      // Total pages
}
```

## Troubleshooting

### Common Issues

1. **Email not sending**
   - Check Gmail app password configuration
   - Verify `admin_notification_email` setting
   - Check server logs for SMTP errors

2. **Database connection errors**
   - Verify database credentials in `.env`
   - Ensure PostgreSQL is running
   - Check database permissions

3. **File upload/download issues**
   - Verify storage configuration
   - Check file permissions
   - Ensure storage directory exists

4. **Authentication errors**
   - Verify Firebase configuration
   - Check token validity
   - Ensure proper headers sent

### Support

For technical support or questions:
- Review API documentation at `/docs`
- Check application logs for error details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

---

**Hexagon Education API** - Empowering education through technology  