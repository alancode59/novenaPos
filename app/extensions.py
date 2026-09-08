from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

# Contadores en memoria: solo valido con un worker (ver el entrypoint).
limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")

login_manager.login_view = "auth.login"


def init_db(app):
    db.init_app(app)
    migrate.init_app(app, db)


def init_auth(app):
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # Import diferido para evitar import circular.
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        user = db.session.get(User, int(user_id))
        if user is None or not user.is_active:
            # Usuario desactivado -> sesion invalida en el siguiente request.
            return None
        return user
