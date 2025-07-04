from flask import Flask, request, jsonify
import os
from api_calls.test_remote_endpoint import run_vertex_ai_inference

app = Flask(__name__)

@app.route('/run_ariae', methods=['POST'])
def run_ariae():
    data = request.json
    input_path = data['input_path']
    output_path = data['output_path']
    try:
        run_vertex_ai_inference(input_path, output_path)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5001) 