README — Ingestion API (FastAPI)
A FastAPI REST API for data ingestion and processing. I separated the code into models, repository, service, and route layers.

The models handle validation and response shapes, the repository owns storage and filtering, the service owns business logic like summary aggregation, and the routes stay thin and handle HTTP concerns.

The app currently is using in-memory storage, but it can be easily swapped with a database by updating the repository layer without changing the rest of the application.


Quick reference for running the app locally and running the test suite.

Prerequisites

Python 3.10+ (3.11/3.12 ok)
Git (optional)
Recommended: use a virtual environment
Setup (one-time)

Create & activate a virtual environment

macOS / Linux
python -m venv .venv
source .venv/bin/activate
Windows (cmd)
python -m venv .venv
.venv\Scripts\activate
Windows (PowerShell)
python -m venv .venv
..venv\Scripts\Activate.ps1
Install dependencies

If you have a requirements.txt:
pip install -r requirements.txt
Otherwise install the essentials:
pip install fastapi uvicorn pydantic pytest httpx
(Optional) Install the package in editable mode so imports work everywhere:

pip install -e .
Run the application (development)

From the project root (the directory that contains app/ and tests/):
uvicorn app.main:app --reload
App will be available at: http://127.0.0.1:8000
Open the interactive docs: http://127.0.0.1:8000/docs

Example requests
Health check:
curl http://127.0.0.1:8000/health

Create event (POST /events):
curl -X POST http://127.0.0.1:8000/events
-H "Content-Type: application/json"
-d '{"customer_id":"alice","resource_id":"r1","metric_name":"cpu","value":12.5}'

Get event:
curl http://127.0.0.1:8000/events/<event_id>

Customer summary:
curl http://127.0.0.1:8000/customers/<customer_id>/summary

Run tests
From the project root, make sure the venv is activated and run:
python -m pytest -q
Or:
pytest -q
If tests fail with "ModuleNotFoundError: No module named 'app'":
Ensure you ran pytest from the project root (where app/ and tests/ live).
Ensure app/init.py exists (so Python treats app as a package).
Or install in editable mode: pip install -e .
Notes & tips

Tests use FastAPI's TestClient and the in-memory repository. The test fixture resets the repository for each test, so tests are isolated.
The in-memory repository (EventRepository) is single-process only. For production use, replace it with a persistent store (DB or Redis).
Keep the server process running for local manual testing; stop with Ctrl+C.
That's it — you should be able to run the API and the tests with the commands above. If you want, I can also provide a requirements.txt or a pyproject.toml/setup.cfg for easier installation.
