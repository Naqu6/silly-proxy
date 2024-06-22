import sys
import threading

from shared import NUM_WORKERS, Job, JobResponse
import requests

import time
import argparse

NUM_WORKERS = 100
requests_served = 0

def worker(work_director_address, local_server_address, model_name):
    global requests_served
    while True:
        try:
            work = requests.get(f"{work_director_address}/get_job")
            
            if work.status_code != 200:
                print("Error")
                continue

            work = work.json()
            if work == {}:
                continue
                
            job = Job(**work)
            job.request_body['model'] = model_name
            response = requests.post(f"{local_server_address}/v1/chat/completions", json=job.request_body, headers={"Authorization": "Bearer fake-key"})

            job_response = JobResponse(id=job.id, response_code=response.status_code, body=response.json())
            requests.post(f"{work_director_address}/submit_job", json=vars(job_response))
            requests_served += 1
        except:
            print("Error")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work_director_address", required=True)
    parser.add_argument("--local_server_address", required=True)
    parser.add_argument("--model_name", required=True)
    args = parser.parse_args()

    for _ in range(NUM_WORKERS):
        t = threading.Thread(target=worker, args=(args.work_director_address, args.local_server_address, args.model_name))
        t.start()

    while True:
        print(f"Requests served: {requests_served}")
        time.sleep(5)

if __name__ == "__main__":
    main()
