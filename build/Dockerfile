FROM python:3.10-alpine
#RUN apk update && apk install musl libblas-dev liblapack-dev libatlas-base-dev gfortran
RUN apk update \
&& apk add --update-cache --no-cache g++ make wget rsync build-base \
&& apk add --update-cache libgcc libquadmath musl \
&& apk add --update-cache --no-cache libgfortran \
&& apk add --update-cache --no-cache lapack-dev

# Установить Node.js и npm
RUN apk add --update-cache --no-cache nodejs npm
# Установить ganache-cli
RUN npm install -g ganache-cli

RUN solc-select install 0.8.19
RUN solc-select use 0.8.19

WORKDIR /app
COPY requirements.txt .
ENV PATH="$PATH:/app/.local/bin"

RUN pip3 install -r requirements.txt

COPY . .
EXPOSE 8082

ENTRYPOINT python src/main.py
