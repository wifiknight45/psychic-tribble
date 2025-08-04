from setuptools import setup, find_packages
from pathlib import Path

here = Path(__file__).parent
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="psychic-tribble",
    version="1.0.0",
    description="Backend for event scheduling with FastAPI and iCalendar export",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="you@example.com",
    url="https://github.com/yourusername/psychic-tribble",
    packages=find_packages(exclude=["tests*", "venv*", ".env*"]),
    python_requires=">=3.8",
    install_requires=[
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
        "pytz>=2021.1",
    ],
    extras_require={
        "dev": [
            "pytest>=6.2",
            "pytest-cov",
            "flake8",
            "mypy",
            "black",
        ]
    },
    entry_points={
        "console_scripts": [
            "psychic-tribble=app:app",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Framework :: FastAPI",
        "License :: OSI Approved :: MIT License",
    ],
)
