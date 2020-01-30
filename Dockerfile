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
COPY run.py /app/

# expose the port
EXPOSE 7507

ENV INNOPOLIS_SSO_BASE https://sso.university.innopolis.ru/adfs

# define the default command to run when starting the container
# CMD ["gunicorn", "--bind", ":7507", "--access-logfile", "-", "run:app"]
# CMD ["flask", "run", "--host=0.0.0.0"]
CMD flask db upgrade && flask run --host=0.0.0.0