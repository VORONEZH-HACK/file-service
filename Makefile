build:
		docker build -t fsp/upload-api . 
run: build 
		docker run --env-file .env -p 10002:8080 fsp/upload-api