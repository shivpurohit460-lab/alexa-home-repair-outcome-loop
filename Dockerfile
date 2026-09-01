FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir .

EXPOSE 8000
CMD ["uvicorn", "alexa_outcome_loop.mcp_server:app", "--host", "0.0.0.0", "--port", "8000"]
