FROM python:3.9-slim

# install OS dependencies
RUN apt-get update
RUN apt-get install -y
RUN apt-get install -y build-essential
RUN apt-get install -y gcc


# install python dependencies
COPY ./ ./app/
WORKDIR /app/
RUN pip install -r requirements.txt

# make a directory for logs
RUN mkdir -p ../logs

# build executable
CMD ["streamlit", "run","app.py"]
