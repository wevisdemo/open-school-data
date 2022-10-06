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

## Output Directory
```
out
└── <year>
    ├── html
    │   ├── area
    │   ├── buidling.html
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


