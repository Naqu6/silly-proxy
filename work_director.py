from flask import Flask, request, jsonify
app = Flask(__name__)
from shared import Job, JobResponse

from collections import deque
import threading
import dataclasses

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
    print(id_, untaken_jobs, inflight_jobs)
    try:
        job_id = untaken_jobs.popleft()
    except IndexError:
        return {}
    
    return vars(inflight_jobs[job_id].job)

@app.route("/submit_job", methods=['POST'])
def submit_job():
    print(id_, untaken_jobs, inflight_jobs)
    response = JobResponse(**request.json)
    assert response.id in inflight_jobs

    inflight_jobs[response.id].response = response
    inflight_jobs[response.id].done_event.set()

    return {"ok": True}

@app.route('/chat/completions', methods=['POST'])
def chat_completions_wrapper():
    global id_
    job = Job(
        id=id_,
        request_body=request.json,
        url='/chat/completions'
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
    app.run(host= '0.0.0.0',debug=True)
