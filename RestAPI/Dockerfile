# pull official base image
FROM python:3.8.6

# set work directory
WORKDIR /usr/src/app
RUN mkdir -p FMUs

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV KUBE_TOKEN
ENV KUBE_HOST

# install dependencies
COPY requirements.txt /usr/src/app
RUN pip3 install -r requirements.txt
# copy project
COPY . /usr/src/app/

EXPOSE 8001

RUN chmod +x ./start.sh
CMD ["./start.sh"]




