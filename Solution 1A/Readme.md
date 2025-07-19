//////////////////////to check if docker is working fine ////////////////////////
nslookup registry-1.docker.io


/////////////to built docker image //////////////////////
docker build --platform linux/amd64 -t pdf-outline-extractor:1a .   


////////////////////to run the main code in windows///////////////////////
docker run --rm `
  -v ${PWD}\input:/app/input `
  -v ${PWD}\output:/app/output `
  --network none `
  pdf-outline-extractor:1a


///////////////to fix broken docker caches and containers /////////////////////////
docker builder prune --all --force
docker system prune -a --volumes



