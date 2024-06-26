from flask import Flask, request, jsonify
app = Flask(__name__)
from shared import Job, JobResponse

from collections import deque
import threading
import dataclasses

MAX_JOBS_PER_REQUEST = 5

id_lock = threading.Lock()
id_ = 0

untaken_jobs = deque()

inflight_jobs = {}

@dataclasses.dataclass
class InflightJob:
    job: Job
    done_event: threading.Event
    response: JobResponse


@app.get("/get_job")
def get_job():
    jobs = []

    for _ in range(MAX_JOBS_PER_REQUEST):
        try:
            job_id = untaken_jobs.popleft()
        except IndexError:
            break
        
        jobs.append(job_id)
        
    return [vars(inflight_jobs[job_id].job) for job_id in jobs]

@app.route("/submit_job", methods=['POST'])
def submit_job():
    response = JobResponse(**request.json)
    assert response.id in inflight_jobs

    inflight_jobs[response.id].response = response
    inflight_jobs[response.id].done_event.set()

    return {"ok": True}

@app.route('/chat/completions', methods=['POST'])
def chat_completions_wrapper():
    global id_

    with id_lock:
        job = Job(
            id=id_,
            request_body=request.json,
        )
        id_ += 1

    assert job.id not in inflight_jobs

    job_done_event = threading.Event()
    job_done_event.clear()

    inflight_jobs[job.id] = InflightJob(job, job_done_event, None)
    untaken_jobs.append(job.id)

    inflight_jobs[job.id].done_event.wait()

    return inflight_jobs[job.id].response.body

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9090)
