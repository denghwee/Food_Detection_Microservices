from app import create_app
import os
app = create_app()
if __name__ == '__main__':
    host = os.getenv('MICRO_HOST', '0.0.0.0')
    port = int(os.getenv('MICRO_PORT', 5002))
    debug = os.getenv('MICRO_DEBUG', '0') in ('1', 'true', 'yes')
    print(f"Starting Flask microservice on {host}:{port}")
    app.run(host=host, port=port, debug=debug)