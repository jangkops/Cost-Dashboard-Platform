from flask import Flask
from dotenv import load_dotenv
from routes.cost_monitoring import cost_monitoring_bp
from routes.finops_routes import finops_bp

load_dotenv()

app = Flask(__name__)

app.register_blueprint(finops_bp)
app.register_blueprint(cost_monitoring_bp, url_prefix='/api/cost-monitoring')

@app.route('/health')
def health():
    return {'status': 'healthy'}, 200

@app.route('/api/cost-monitoring/health')
def cost_health():
    return {'status': 'healthy', 'service': 'cost-monitoring'}, 200

@app.errorhandler(Exception)
def handle_exception(e):
    import traceback
    traceback.print_exc()
    return str(e), 500

import boto3
try:
    boto3.client('sts').get_caller_identity()
    print('AWS credentials initialized')
except:
    print('AWS credentials not available')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
