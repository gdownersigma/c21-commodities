FROM public.ecr.aws/lambda/python:3.12

COPY price_alerts_requirements.txt ${LAMBDA_TASK_ROOT}/

RUN pip install --no-cache-dir -r price_alerts_requirements.txt

COPY alert.py.py ${LAMBDA_TASK_ROOT}/
COPY generate_alert.py ${LAMBDA_TASK_ROOT}/
COPY Logo.png ${LAMBDA_TASK_ROOT}/

CMD ["alert.handler"]
