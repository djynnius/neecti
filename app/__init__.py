from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_cors import CORS
import os
import logging

# Initialize extensions
db = SQLAlchemy()
socketio = SocketIO()
migrate = Migrate()
bcrypt = Bcrypt()
login_manager = LoginManager()
cors = CORS()

def create_app():
    app = Flask(__name__)

    # Load configuration
    app.config.from_object('app.config.Config')

    # Configure logging
    if not app.debug:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
    
    # Initialize extensions with app
    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Configure CORS
    cors.init_app(app,
                  origins=[
                      "https://localhost:8443",
                      "http://localhost:3000",
                      "https://co.nnecti.ng",
                      "http://co.nnecti.ng"
                  ],
                  supports_credentials=True,
                  allow_headers=["Content-Type", "Authorization"],
                  methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.posts import posts_bp
    from app.routes.users import users_bp
    from app.routes.messages import messages_bp
    from app.routes.api import api_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(api_bp)

    # Import SocketIO event handlers
    from app.controllers import socketio_controller

    return app
