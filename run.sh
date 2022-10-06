#!/bin/bash

python url_indexer.py

python scrape_pages.py &
scrape_pages_pid=$!

python scrape_buildings.py &
scrape_buildings_pid=$!

wait $scrape_pages_pid
wait $scrape_buildings_pid
echo "html files are ready"

python structuring.py