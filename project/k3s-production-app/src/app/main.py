from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Load configuration from environment variables
app.config['DATABASE_URI'] = os.getenv('DATABASE_URI', 'postgresql://user:password@localhost/dbname')
app.config['REDIS_URL'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

@app.route('/')
def home():
    return "Welcome to the K3s Production App!"

@app.route('/data', methods=['POST'])
def handle_data():
    data = request.json
    # Process the data (this is just a placeholder)
    return jsonify({"message": "Data received", "data": data}), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)