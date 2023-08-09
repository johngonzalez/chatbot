FROM python:3.11.1

COPY requirements.txt /opt/program/
RUN pip install --trusted-host pypi.python.org -r /opt/program/requirements.txt

COPY . /opt/program

WORKDIR /opt/program

EXPOSE 8080

ENTRYPOINT ["python", "main.py"]