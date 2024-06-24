from pydantic import BaseModel

class Job(BaseModel):
    id: int
    request_body: dict

class JobResponse(BaseModel):
    id: int
    response_code: int
    body: dict
