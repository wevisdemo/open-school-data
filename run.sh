#!/bin/bash

python src/province.py && python src/school_scraper.py && python src/school_pages.py && python src/school_pages_scraper.py  &
python src/school_building.py
python src/school.py
python src/download_images.py
