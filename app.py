import sys
from flask import Flask
from routes.users import users_bp
from routes.events import events_bp
from routes.timeslots import timeslots_bp
from routes.calendar import calendar_bp

def create_app():
    app = Flask(__name__)

    # Optional: ngrok in Colab
    if 'google.colab' in sys.modules:
        try:
            from flask_ngrok import run_with_ngrok
            run_with_ngrok(app)
        except ImportError:
            pass

    # Register Blueprints
    app.register_blueprint(users_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(timeslots_bp)
    app.register_blueprint(calendar_bp)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
