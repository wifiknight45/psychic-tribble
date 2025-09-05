Psychic-Tribble 
A secure, intuitive calendar and event management platform built for modern teams and individuals. Psychic-Tribble offers seamless scheduling, calendar synchronization, and a powerful API—all wrapped in a fast, scalable FastAPI backend.
<!-- START STRUCTURE -->
<!-- END STRUCTURE -->




Psychic-Tribble is a modern task management application that provides a robust backend API with enterprise-grade security features, comprehensive monitoring, and scalable architecture. The platform is designed to handle task management operations with built-in rate limiting, CORS support, and comprehensive error handling.

Features
SecDevOps approach
HTTPS Redirect: Automatic redirection to secure connections
CORS Protection: Configurable cross-origin resource sharing
Security Headers: Custom security middleware for enhanced protection
Rate Limiting: Built-in request throttling to prevent abuse

Monitoring & Observability
Comprehensive Logging: Structured logging with configurable levels
Metrics Integration: Built-in performance and health monitoring
Error Tracking: Global exception handling with detailed logging

Performance & Scalability
FastAPI Framework: High-performance async Python web framework
Modular Architecture: Clean separation of concerns with organized routing
Middleware Pipeline: Optimized request processing chain

Developer Experience
Auto-generated Documentation: Interactive API docs at /docs and /redoc
OpenAPI Specification: Complete API specification available at /openapi.json
Type Safety: Full type hints throughout the codebase

Prerequisites
Python 3.8+
FastAPI
Required dependencies (see Installation section)

Installation
step 1: Clone the repository
# bash
git clone https://github.com/wifiknight45/psychic-tribble.git
cd psychic-tribble

step 2: Create a virtual environment
# bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

Install dependencies
bashpip install -r requirements.txt

Set up environment variables
Create a .env file in the project root:
env# CORS Configuration
ALLOWED_CORS_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]

# Security Settings
ENABLE_HTTPS_REDIRECT=false  # Set to true in production

# Rate Limiting
DEFAULT_RATE_LIMIT="100/minute"

# Add other configuration variables as needed


Usage
Development Server
Start the development server:
bashuvicorn psychic_tribble.main:app --reload --host 0.0.0.0 --port 8000
The API will be available at:

API Base: http://localhost:8000
Interactive Docs: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc
Health Check: http://localhost:8000/

Production Deployment
# bash method 1--> Using Gunicorn with Uvicorn workers
gunicorn psychic_tribble.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# bash method 2--> Or with Docker (Dockerfile)
docker build -t psychic-tribble .
docker run -p 8000:8000 psychic-tribble

Project Structure
add more here my file directory is complex af rn

API Endpoints
The application provides a modular API structure. Key endpoints include:

GET / - Health check and API status
GET /docs - Interactive API documentation
GET /redoc - Alternative API documentation
GET /openapi.json - OpenAPI specification

Additional endpoints are defined in the modular API routers.
Configuration
The application uses a settings-based configuration system. Key configuration options:

CORS Origins: Configure allowed cross-origin domains
HTTPS Redirect: Enable/disable automatic HTTPS redirection
Rate Limiting: Set default rate limits for API endpoints
Logging Level: Configure application logging verbosity

Security Features
Rate Limiting
Built-in protection against API abuse with configurable rate limits:
python# Default: 100 requests per minute per IP
DEFAULT_RATE_LIMIT="100/minute"
CORS Protection
Configurable cross-origin resource sharing:
python# Allow specific origins
ALLOWED_CORS_ORIGINS=["https://INPUTcoolWebSiteHEREbruh.com"]
Security Headers
Custom middleware adds security headers to all responses for enhanced protection against common web vulnerabilities.
Error Handling
The application includes comprehensive error handling:

Global Exception Handler: Catches and logs all unhandled exceptions
Custom Exception Handlers: Specific handling for different error types
Rate Limit Exceptions: Graceful handling of rate limit violations
Structured Error Responses: Consistent error response format

Monitoring & Logging
Structured logging with configurable levels
Request/response logging
Error tracking with stack traces
Performance monitoring

Metrics
Built-in metrics collection
Performance monitoring
Health check endpoints
Custom metric support

Authorized Developer Collaborators:

Fork the repository
Create a feature branch (git checkout -b feature/amazing-feature)
Commit your changes (git commit -m 'Add amazing feature')
Push to the branch (git push origin feature/amazing-feature)
Open a Pull Request

Development Guidelines
Follow PEP 8 style guidelines
Add type hints to all functions
Write comprehensive tests
Update documentation for new features
Ensure all security middleware remains intact

Testing
# bash 
Run tests
pytest

# Run with coverage
pytest --cov=psychic_tribble

# Run specific test file
pytest tests/test_main.py
License
This project is licensed under the MIT License - see the LICENSE file for details.
Support

Email: wifiknight45@proton.me
Website tbd after front end dev

Documentation: Available at /docs when running the application

Roadmap (subject to change)
 Add authentication and authorization
 Implement task CRUD operations
 Add user management system
 WebSocket support for real-time updates
 Database integration
 Caching layer implementation
 Comprehensive test suite
 Docker containerization
 CI/CD pipeline setup

Development
Robert Hodgkiss 
wifiknight45@proton.me

Business and Marketing
Crystal Andrews 
andrews.crystal@gmail.com

⚠️ Proprietary Software Notice ⚠️ 
This codebase is proprietary and confidential. Unauthorized use, copying, modification, or distribution is prohibited. For access or licensing inquiries, contact the development team.
For questions, bug reports, or feature requests, please reach out to the development team at wifiknight45@proton.me

Psychic-Tribble - Seamless event planning for the modern world
Copyright © 2025 Psychic Tribble. All rights reserved.
This software is proprietary and confidential. Unauthorized use is prohibited without written permission from the authors.

Built with ❤️ using FastAPI and modern Python practices.
