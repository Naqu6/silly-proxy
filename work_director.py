from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict
from collections import deque
import threading

from shared import Job, JobResponse

MAX_JOBS_PER_REQUEST = 5

id_ = 0
untaken_jobs = deque()
inflight_jobs = {}

class InflightJob:
    def __init__(self, job: Job, done_event: threading.Event):
        self.job = job
        self.done_event = done_event
        self.response = None

app = FastAPI()

@app.get("/get_job")
def get_job():
    jobs = []

    for _ in range(MAX_JOBS_PER_REQUEST):
        try:
            job_id = untaken_jobs.popleft()
        except IndexError:
            break
        
        jobs.append(job_id)
        
    return [inflight_jobs[job_id].job.dict() for job_id in jobs]

@app.post("/submit_job")
def submit_job(response: JobResponse):
    assert response.id in inflight_jobs

    inflight_jobs[response.id].response = response
    inflight_jobs[response.id].done_event.set()

    return {"ok": True}

@app.post('/chat/completions')
def chat_completions_wrapper(request: Request):
    global id_
    request_body = request.json()
    job = Job(
        id=id_,
        request_body=request_body,
    )
    id_ += 1

    assert job.id not in inflight_jobs

    job_done_event = threading.Event()
    job_done_event.clear()

    inflight_jobs[job.id] = InflightJob(job, job_done_event)
    untaken_jobs.append(job.id)

    inflight_jobs[job.id].done_event.wait()

    return JSONResponse(inflight_jobs[job.id].response.body)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=9090)
