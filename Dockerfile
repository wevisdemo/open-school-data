FROM python:3
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY ./helpers ./helpers
COPY scrape_pages.py .
COPY scrape_buildings.py .
COPY structuring.py .
COPY run.sh .
COPY url_indexer.py .
COPY header_mapper.json .
CMD ./run.sh