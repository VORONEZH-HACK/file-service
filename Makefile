build:
		docker build -t fsp/upload-api . 
run: build 
		docker run -p 10002:8080 fsp/upload-api