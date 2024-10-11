FROM python:3.9-slim

WORKDIR /load-balancer

COPY . /load-balancer

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "load_balancer.py"]