export VERSION=1.2.01
export PROJECT="woodworkapi"
export USERNAME="iaggo"
export REPOSITORY="woodwork4.0_api"

docker build -t ${REPOSITORY} .

docker image tag ${REPOSITORY} ${USERNAME}/${REPOSITORY}:${VERSION}

docker image  push  ${USERNAME}/${REPOSITORY}:${VERSION}
