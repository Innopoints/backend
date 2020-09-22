FROM python:3.8.1

RUN mkdir -p /app
WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install our dependencies
# we use --system flag because we don't need an extra virtualenv
COPY Pipfile Pipfile.lock /app/
RUN pip install --upgrade pip
RUN pip install pipenv && pipenv install --system

# copy the project code
COPY innopoints /app/innopoints
COPY migrations /app/migrations
COPY templates /app/templates
COPY run.py /app/

# expose the port
EXPOSE 7507

ENV INNOPOLIS_SSO_BASE https://sso.university.innopolis.ru/adfs
ENV FLASK_APP run.py
ENV FLASK_RUN_PORT 7507
ENV FLASK_ENV development

VOLUME [ "/app/static_files" ]

# define the default command to run when starting the container
CMD [ "flask", "run", "--host=0.0.0.0"]
