FROM public.ecr.aws/lambda/python:3.12

COPY report_requirements.txt ${LAMBDA_TASK_ROOT}/

RUN pip install --no-cache-dir -r report_requirements.txt

COPY report_extract.py ${LAMBDA_TASK_ROOT}/
COPY report_generate.py ${LAMBDA_TASK_ROOT}/
COPY Logo.png ${LAMBDA_TASK_ROOT}/

CMD ["report_generate.handler"]
