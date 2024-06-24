import dataclasses

@dataclasses.dataclass
class Job:
    id: int
    request_body: dict

@dataclasses.dataclass
class JobResponse:
    id: int
    response_code: int
    body: dict
