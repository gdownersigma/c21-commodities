FROM python:3.12-slim

WORKDIR /app

COPY dashboard_requirements.txt .
RUN pip install --no-cache-dir -r dashboard_requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
