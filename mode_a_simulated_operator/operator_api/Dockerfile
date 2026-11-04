FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mode_a_simulated_operator/operator_api/main.py .

EXPOSE 8000

CMD ["python", "main.py"]
