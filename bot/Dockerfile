FROM python:3.12-alpine

WORKDIR /root/.project

COPY requirements.txt .

RUN pip install -r requirements.txt

RUN playwright install

COPY src .

CMD ["python", "main.py"]