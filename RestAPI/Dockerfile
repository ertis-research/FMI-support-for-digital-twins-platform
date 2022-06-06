# pull official base image
FROM python:3.8.6

# set work directory
WORKDIR /usr/src/app
RUN mkdir -p FMUs

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# set kubernetes token
ENV KUBE_TOKEN
# set kubernetes host
ENV KUBE_HOST

# install dependencies
RUN pip install --upgrade pip
RUN pip install kubernetes
RUN pip install flask
RUN pip install waitress

# copy project
COPY . /usr/src/app/

EXPOSE 8001

RUN chmod +x ./start.sh
CMD ["./start.sh"]