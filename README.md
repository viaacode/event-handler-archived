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

4. Run the tests with:

    `$ pytest -v`

5. Run the application:

   `$ uwsgi -i uwsgi.ini`

The application is now serving requests on `localhost:8080`. Try it with:

```
$ curl -v -X GET localhost:8080/health/live
```

#### Testing different events

Different events (as XML-files) are stored under `./tests/resources/`. Try them with:

##### Single event

```bash
$ curl -i -X POST \
    -H "Content-type: text/xml; charset=utf-8" \
    --data-binary @tests/resources/single_premis_event.xml \
    localhost:8080/event
```

##### Multiple events in one payload

```bash
$ curl -i -X POST \
    -H "Content-type: text/xml; charset=utf-8" \
    --data-binary @tests/resources/multi_premis_event.xml \
    localhost:8080/event
```

##### Invalid event

```bash
$ curl -i -X POST \
    -H "Content-type: text/xml; charset=utf-8" \
    --data-binary @tests/resources/invalid_premis_event.xml \
    localhost:8080/event
```

##### Invalid XML payload

```bash
$ curl -i -X POST \
    -H "Content-type: text/xml; charset=utf-8" \
    --data-binary @tests/resources/invalid_xml_event.xml \
    localhost:8080/event
```

These should return proper informative messages to the client caller.


### Running using Docker

1. Build the container:

   `$ docker build . -t event-handler-archived`

2. Run the container:

   `$ docker run -p 8080:8080 event-handler-archived`

You can try the same cURL commands as specified above.
