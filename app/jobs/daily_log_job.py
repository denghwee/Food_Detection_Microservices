def daily_log_job(app):
    print("Daily log job START")

    with app.app_context():
        from app.services.daily_log_service import create_daily_logs_for_all_users
        create_daily_logs_for_all_users()

    print("Daily log job END")
