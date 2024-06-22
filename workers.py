import sys
import threading

from shared import NUM_WORKERS, Job, JobResponse
import requests

import time

requests_served = 0

def worker(work_director_address, local_server_address):
    while True:
        work = requests.get(f"{work_director_address}/get_job")
        
        if work.status_code != 200:
            print("Error")
            continue

        work = work.json()
        if work == {}:
            continue
            
        job = Job(**work)

        response = requests.post(f"{local_server_address}/{job.url}", json=job.request_body)

        job_response = JobResponse(id=job.id, response_code=response.status_code, body=response.json())
        requests.post(f"{work_director_address}/submit_job", json=vars(job_response))
        requests_served += 1


def main(work_director_address, local_server_address):
    for _ in NUM_WORKERS:
        t = threading.Thread(target=worker, args=(work_director_address, local_server_address))
        t.start()

    while True:
        print(f"Requests served: {requests_served}")
        time.sleep(5)

if __name__ == "__main__":
    main(work_director_address=sys.argv[1], local_server_address=sys.argv[2])