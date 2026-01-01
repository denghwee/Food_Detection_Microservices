from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from .config import Config
from .routes import register_routes
from .extensions import db, jwt, migrate, scheduler
from .jobs.daily_log_job import daily_log_job

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
            user_profile_weight_history
        )
        db.create_all()

    from app.controllers.calorie_controller import calorie_bp
    app.register_blueprint(calorie_bp)
    from app.controllers.food_detection_controller import food_detection_bp
    app.register_blueprint(food_detection_bp)

    app.config["SCHEDULER_API_ENABLED"] = True

    scheduler.init_app(app)
    scheduler.start()

    # chạy mỗi ngày lúc 00:00
    scheduler.add_job(
        id="daily_log_job",
        func=daily_log_job,
        args = [app],
        trigger="cron",
        hour=0,
        minute=0
    )
    #  chạy mỗi ngày lúc 00:00
    # scheduler.add_job(
    #     id="daily_log_job",
    #     args=[app],
    #     func=daily_log_job,
    #     trigger="interval",
    #     minutes=1
    # )

    from app.controllers.user_profile_controller import user_profile_bp
    app.register_blueprint(user_profile_bp)

    from app.services.daily_log_service import create_daily_logs_for_all_users
    from app.controllers.daily_log_controller import daily_log_bp
    app.register_blueprint(daily_log_bp)


    return app
