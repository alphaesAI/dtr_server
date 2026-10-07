import os

from dotenv import load_dotenv

load_dotenv()


def public_fhir_base_url() -> str:
    return os.getenv("PUBLIC_FHIR_BASE_URL", "http://localhost:8000/fhir").rstrip("/")
