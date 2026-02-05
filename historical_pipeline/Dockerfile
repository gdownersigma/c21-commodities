FROM public.ecr.aws/lambda/python:3.12

WORKDIR ${LAMBDA_TASK_ROOT}

COPY historical_requirements.txt .
RUN pip install --no-cache-dir -r historical_requirements.txt

COPY historical_extract.py .

COPY historical_transform.py .

COPY historical_load.py .

COPY historical_pipeline.py .

CMD ["historical_pipeline.handler"]