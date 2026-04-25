# Judge Service

FastAPI service that runs submitted Python code in a disposable worker process.

## Local Run

```powershell
cd judge_service
py -3 -m pip install -r requirements.txt
$env:JUDGE_API_TOKEN="dev-secret"
py -3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Then configure the Streamlit app:

```powershell
$env:JUDGE_API_URL="http://localhost:8000"
$env:JUDGE_API_TOKEN="dev-secret"
streamlit run streamlit_app.py
```

## Environment Variables

- `JUDGE_API_TOKEN`: shared secret required by Streamlit.
- `MAX_SUBMISSION_SECONDS`: wall-clock timeout per submission, default `10`.
- `MAX_TEST_CASES`: max test cases per request, default `100`.
- `MAX_WORKER_MEMORY_MB`: best-effort Linux worker memory cap, default `512`.
- `MAX_WORKER_CPU_SECONDS`: best-effort Linux worker CPU cap, default `8`.

## Docker

Build from inside this folder:

```powershell
docker build -t competition-judge .
docker run -p 8000:8000 -e JUDGE_API_TOKEN=dev-secret competition-judge
```

Or build from the repository root:

```powershell
docker build -f Dockerfile.judge -t competition-judge .
docker run -p 8000:8000 -e JUDGE_API_TOKEN=dev-secret competition-judge
```
