# Inherites a base mage to use
FROM python:3.8-slim-buster

# Use same dir and name for rest of ops
WORKDIR /1779_A1_backend

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

EXPOSE 5001
CMD ["python", "Lab1/run.py"]