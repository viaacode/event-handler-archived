# Event handler: Archived

## Synopsis

Handles incoming webhooks from Mediahaven. It transforms the incoming event and
forwards it to a Rabbit queue.

## Prerequisites

- Git
- Docker
- Python 3.6+
- Linux (if you want to run it locally, uwsgi is not available on other
  platforms.)
- Access to the [meemoo PyPi](http://do-prd-mvn-01.do.viaa.be:8081)

## Usage

1. Clone this repository with:

   `$ git clone https://github.com/viaacode/event-handler-archived.git`

2. Change into the new directory.

### Running locally

**Note**: As per the aforementioned requirements, this is a Python3
application. Check your Python version with `python --version`. You may want to
substitute the `python` command below with `python3` and if your Python version
is < 3.

1. Start by creating a virtual environment:

   `$ python -m venv env`

2. Activate the virtual environment:

    `$ source env/bin/activate`

3. Install the external modules:

   ```
   $ pip install -r requirements.txt \
        --extra-index-url http://do-prd-mvn-01.do.viaa.be:8081/repository/pypi-all/simple \
        --trusted-host do-prd-mvn-01.do.viaa.be
   ```

4. Run the application:

   `$ uwsgi -i uwsgi.ini`

The application is now serving requests on `localhost:8080`. Try it with:

```
$ curl -X GET localhost:8080/health/live
```

### Running using Docker

1. Build the container:

   `$ docker build . -t mediahaven2vrt`

2. Run the container:

   `$ docker run -p 8080:8080 mediahaven2vrt`
