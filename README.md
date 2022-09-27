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
  -v $(pwd)/data:/usr/src/app/out \
  opensd
```
