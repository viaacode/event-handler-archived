# Mediahaven2VRT

## Synopsis

Handles incoming webhooks from Mediahaven. It transforms the incoming event and puts it on a Rabbit queue.

## Prerequisites

- Git
- Docker
- Python (3.6+)
- Linux (if you want to run it locally, uwsgi is not available on other platforms.)
- Access to the (VIAA PyPi)[http://do-prd-mvn-01.do.viaa.be:8081]

## Usage

1. Clone this repository with `git clone`
2. Change into the new directory.

### Local 

1. Start by creating a virtual environment `python -m venv env`.
2. Install the external modules using `$ pip install -r requirements.txt`.
3. You should be able to run this project using `$ uwsgi -i uwsgi.ini`.

### Docker

1. Build the container with `$ docker build . -t mediahaven2vrt`
2. Run the container with `$ docker run -p 8080:8080 mediahaven2vrt`
