import dataclasses

NUM_WORKERS = 100

@dataclasses.dataclass
class Job:
    id: int
    request_body: dict
    url: str

@dataclasses.dataclass
class JobResponse:
    id: int
    response_code: int
    body: dict
