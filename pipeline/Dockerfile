FROM public.ecr.aws/lambda/python:3.12

WORKDIR ${LAMBDA_TASK_ROOT}

COPY pipeline_requirements.txt .
RUN pip install -r pipeline_requirements.txt

COPY extract.py .

COPY transform.py .

COPY load.py .

COPY pipeline.py .


CMD ["pipeline.handler"]