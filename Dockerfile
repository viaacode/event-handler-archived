FROM python:3.6-slim-stretch

# Applications should run on port 8080 so NGINX can auto discover them.
EXPOSE 8080

# Make a new group and user so we don't run as root.
RUN addgroup --system appgroup && adduser --system appuser --ingroup appgroup

WORKDIR /app

# Let the appuser own the files so he can rwx during runtime.
COPY . .
RUN chown -R appuser:appgroup /app

# Install gcc and libc6-dev to be able to compile uWSGI
RUN apt-get update && \
    apt-get install --no-install-recommends -y gcc libc6-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# We install all our Python dependencies. Add the extra index url because some
# packages are in the meemoo repo.
RUN pip3 install -r requirements.txt \
    --extra-index-url http://do-prd-mvn-01.do.viaa.be:8081/repository/pypi-all/simple \
    --trusted-host do-prd-mvn-01.do.viaa.be && \
    pip3 install flake8

USER appuser

# This command will be run when starting the container. It is the same one that
# can be used to run the application locally.
ENTRYPOINT [ "uwsgi", "-i", "uwsgi.ini"]
