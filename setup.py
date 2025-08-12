[build-system]
requires = ["setuptools>=62", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "psychic-tribble"
version = "1.0.0"
description = "Backend for event scheduling with FastAPI and iCalendar export"
readme = "README.md"
license = { file = "LICENSE" }
authors = [
    { name = "Psychic Tribble Dev Team" }
]
requires-python = ">=3.8"
dependencies = [
    "fastapi>=0.70.0",
    "uvicorn[standard]>=0.15.0",
    "sqlalchemy>=1.4.0",
    "alembic>=1.7.0",
    "pydantic>=1.8.0",
    "passlib[bcrypt]>=1.7.0",
    "python-jose[cryptography]>=3.2.0",
    "slowapi>=0.1.4",
    "redis>=4.0.0",
    "icalendar>=4.0.0",
    "pytz>=2021.1"
]
keywords = ["calendar", "fastapi", "icalendar", "scheduler", "psychic tribble"]
classifiers = [
    "License :: Other/Proprietary License",
    "Programming Language :: Python :: 3",
    "Framework :: FastAPI",
    "Operating System :: OS Independent"
]

[project.optional-dependencies]
dev = [
    "pytest>=6.2",
    "pytest-cov>=3.0.0",
    "flake8>=6.0.0",
    "mypy>=1.5,<1.6",
    "black>=23.3,<24.0",
    "build",
    "twine"
]

[project.urls]
Homepage = "https://psychictribble.dev"
Source = "https://github.com/wifiknight45/psychic-tribble"

[tool.setuptools]
include-package-data = true
packages = ["app"]

[tool.setuptools.packages.find]
exclude = ["tests*", "venv*", ".env*"]

[tool.setuptools.entry-points.console_scripts]
psychic-tribble = "app:app"

