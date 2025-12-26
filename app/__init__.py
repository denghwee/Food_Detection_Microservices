from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from .config import Config
from .routes import register_routes
from .extensions import db, jwt, migrate


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    Config.init_cloudinary()
    register_routes(app)

    with app.app_context():
        from app.models import (
            user_profile,
            daily_energy_log,
            food_record,
            activity,
            user_profile_weight_history
        )
        db.create_all()

    from app.controller.calorie_controller import calorie_bp
    app.register_blueprint(calorie_bp)

    from app.controller.calorie_out_controller import calorie_out_bp
    app.register_blueprint(calorie_out_bp)

    from app.controller.user_profile_controller import user_profile_bp
    app.register_blueprint(user_profile_bp)

    from app.services.daily_log_service import create_daily_logs_for_all_users
    from app.controller.daily_log_controller import daily_log_bp
    app.register_blueprint(daily_log_bp)
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=create_daily_logs_for_all_users,
        trigger="cron",
        hour=0,
        minute=0
    )
    scheduler.start()

    return app
