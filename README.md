# Open School Data

## Using Docker
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

run it uting shell
```
./run.sh
```