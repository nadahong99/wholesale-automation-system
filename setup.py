# setup.py
from setuptools import setup, find_packages

setup(
    name="wholesale-automation-system",
    version="1.0.0",
    description="AI-powered Korean wholesale automation platform",
    packages=find_packages(exclude=["tests*", "scripts*"]),
    python_requires=">=3.11",
    install_requires=[
        "fastapi>=0.115",
        "uvicorn[standard]>=0.30",
        "pydantic>=2.9",
        "pydantic-settings>=2.5",
        "sqlalchemy>=2.0",
        "requests>=2.32",
        "beautifulsoup4>=4.12",
        "celery>=5.4",
        "redis>=5.1",
        "python-telegram-bot>=21.7",
        "google-cloud-storage>=2.18",
        "Pillow>=11.0",
        "streamlit>=1.39",
        "pandas>=2.2",
        "python-dotenv>=1.0",
    ],
)
