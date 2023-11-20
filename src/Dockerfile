FROM python:3.9-slim

# install OS dependencies
RUN apt-get update
RUN apt-get install -y
RUN apt-get install -y build-essential
RUN apt-get install -y gcc


# copy the src folder to the ./app/ folder (copies all files expect those in .dockerignore)
COPY ./ ./app/

# go to the app folder
WORKDIR /app/

# install python dependencies
RUN pip install -r requirements.txt

# make a directory for logs
RUN mkdir -p ../logs

WORKDIR /app/static/
RUN python gen_pwd.py credentials.yml

WORKDIR /app/

# build executable
CMD ["streamlit", "run","app.py"]
