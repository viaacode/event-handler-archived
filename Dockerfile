FROM python:3.6-slim-stretch

# Applications should run on port 8080 so NGINX can auto discover them.
EXPOSE 8080

# This is the location where our files will go in the container.
VOLUME /usr/src/app
WORKDIR /usr/src/app

# Copy all files
COPY . .

# Install gcc and libc6-dev to be able to compile uWSGI
RUN apt-get update && \
    apt-get install --no-install-recommends -y gcc libc6-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# We install all our Python dependencies. Add the extra index url because some
# packages are in the meemoo repo.
RUN pip3 install -r requirements.txt \
    --extra-index-url http://do-prd-mvn-01.do.viaa.be:8081/repository/pypi-all/simple \
    --trusted-host do-prd-mvn-01.do.viaa.be

# This command will be run when starting the container. It is the same one that
# can be used to run the application locally.
ENTRYPOINT [ "uwsgi", "-i", "uwsgi.ini"]
