# Open School Data

## 🐳 Using Docker

First, build image

```sh
docker build -t opensd .
```

And run it!

```sh
docker run -it --rm \
  --name openschooldata \
  -v $(pwd)/out:/usr/src/app/out \
  opensd
```

## Run it locally

Install requirements

```
pip install -r requirements.txt
```

run it

```
./run.sh
```

## Overview

![](/imgs/overview.png)

`scrape_buildings.py` and `scrape_pages.py` will run in the background simultaneously when you run it by `run.sh`.

## Output Directory

```
out
└── <year>
    ├── html
    │   ├── area
    │   ├── province
    │   └── school
    ├── school_data
    │   ├── school
    │   │   ├── <school_id>
    │   │   │   └── <...>.csv
    │   │   └── <schol_id>
    │   │       ├── building.csv
    │   │       ├── computer.csv
    │   │       ├── durable_goods.csv
    │   │       ├── general.csv
    │   │       ├── internet.csv
    │   │       ├── staff.csv
    │   │       └── student.csv
    │   ├── building.csv
    │   ├── computer.csv
    │   ├── durable_goods.csv
    │   ├── general.csv
    │   ├── internet.csv
    │   ├── staff.csv
    │   └── student.csv
    ├── open_school_data.log
    ├── <indexer..>
    └── <indexer..>
```

## Configering

mapping from table column C to D by configering in [`header_mapper.json`](header_mapper.json)

```json
{
    feild_name: {old_col_name_C0: new_col_name_D0, old_col_name_C1: new_col_name_D1, ...},
    feild_name: {old_col_name_C0: new_col_name_D0, old_col_name_C1: new_col_name_D1, ...},
    feild_name: {old_col_name_C0: new_col_name_D0, old_col_name_C1: new_col_name_D1, ...},
}
```
if the new column name D is empty, then it will be the same.