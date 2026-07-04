import uuid

from workers.config import settings


def generate_trace_id() -> str:
    return f"trace_{uuid.uuid4().hex[:12]}"


def generate_request_id() -> str:
    return f"req_{uuid.uuid4().hex[:12]}"


def extract_trace_id(headers: dict[str, str]) -> str | None:
    return headers.get(settings.trace_id_header)