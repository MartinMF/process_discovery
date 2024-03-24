from flask import request, jsonify, render_template, Response
from app.miner import *

from app import app


@app.route('/')
def home_route():
    return render_template('index.html')


@app.route("/digraph", methods=["POST"])
def get_digraph_endpoint():
    try:
        get_log_txt_from_server()
        data = request.json
        process_name = data["process_name"]
        digraph = get_digraph_from_json_log(process_name)
        return jsonify(message=digraph)
    except Exception as e:
        return jsonify(error=str(e)), 500


# Retrieve the current traces
@app.route("/traces", methods=["POST"])
def get_traces_endpoint():
    try:
        # traces = get_traces().replace("ε", "&#949;")
        data = request.json
        process_name = data["process_name"]
        traces = get_traces_from_json_log(process_name)
        return jsonify(message=traces)
    except Exception as e:
        return jsonify(error=str(e)), 500


# Updates the activity_data.json and returns json
@app.route("/activity_data", methods=["GET"])
def update_activity_data_endpoint():
    try:
        get_log_txt_from_server()

        data = update_activity_data()
        return jsonify(data)
    except Exception as e:
        return jsonify(error=str(e)), 500


# Starts the selected process a given amount of times
@app.route("/start_process_instances", methods=["POST"])
def start_process_instances_endpoint():
    try:
        data = request.json
        process_name = data["process_name"]
        amount = data["amount"]
        start_process_instances(process_name, amount)
        return jsonify(message="Started process instances")
    except Exception as e:
        return jsonify(error=str(e)), 500


# Clears all contents if the log.txt
@app.route("/clear_logs", methods=["GET"])
def clear_logs_endpoint():
    try:
        clear_log_txt()
        clear_activity_data_json()
        return jsonify(message="Cleared all logs!")
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route('/events')
def events():
    return Response(monitor_remote_file(), content_type='text/event-stream')
