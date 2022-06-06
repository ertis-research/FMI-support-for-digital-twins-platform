FROM continuumio/miniconda3
MAINTAINER XenonStack

# set work directory
WORKDIR /usr/src/app

# copy project
COPY . /usr/src/app/

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN conda create --name env
RUN conda update conda
RUN conda config --add channels conda-forge
RUN conda install pyfmi
RUN conda install flask
RUN conda install kafka-python
#RUN conda install kubernetes

EXPOSE 8001

RUN chmod +x ./start.sh
CMD ["./start.sh"]