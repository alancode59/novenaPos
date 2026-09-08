import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-env")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "mysql+pymysql://posnovena:posnovena@mysql:3306/posnovena",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"
