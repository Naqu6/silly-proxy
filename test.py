import threading
import time
import requests
from flask import Flask, request, jsonify
import subprocess
import signal
import logging

NUM_REQUESTS = 100


def create_mock_server(port):
    app = Flask("mock_server")
    @app.route("/v1/chat/completions", methods=["POST"])
    def chat_completions():
        data = request.json
        response_body = {
            "message": f"Processed by mock server on port {port}",
            "data": data["index"],
        }
        return jsonify(response_body), 200
    app.run(host="0.0.0.0", port=port)


# Function to start work_director process
def start_work_director():
    process = subprocess.Popen(
        ["python3", "work_director.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return process


# Function to start workers process
def start_workers(work_director_address, local_server_address, model_name):
    process = subprocess.Popen(
        [
            "python3",
            "workers.py",
            "--work_director_address",
            work_director_address,
            "--local_server_address",
            local_server_address,
            "--model_name",
            model_name,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return process


def main():
    # Start the work_director service
    work_director_process = start_work_director()

    # Start a single mock server
    mock_server_port = 5001
    mock_server_thread = threading.Thread(
        target=create_mock_server, args=(mock_server_port,)
    )
    mock_server_thread.daemon = True
    mock_server_thread.start()

    # Let the servers startup
    time.sleep(2)

    # Start workers
    workers_process = start_workers(
        "http://localhost:9090", f"http://localhost:{mock_server_port}", "test-model"
    )

    response = requests.post(
        "http://localhost:9090/chat/completions",
        json={"input": f"Test input {0}", "index": 0},
    )

    if True:
        # try:
        responses = []

        def make_request(index):
            response = requests.post(
                "http://localhost:9090/chat/completions",
                json={"input": f"Test input {index}", "index": index},
            )
            responses.append(response.json())

        threads = []
        for i in range(NUM_REQUESTS):
            t = threading.Thread(target=make_request, args=(i,))
            t.start()
            threads.append(t)
            time.sleep(0.005)

        for thread in threads:
            thread.join()


        assert len({response['data'] for response in responses}) == NUM_REQUESTS
        # finally:
        workers_process.send_signal(signal.SIGKILL)
        workers_process.wait()

        # Terminate the processes
        work_director_process.send_signal(signal.SIGKILL)
        work_director_process.wait()


if __name__ == "__main__":
    main()
