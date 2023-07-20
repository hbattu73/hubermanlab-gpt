# Running Locally
## With Docker
```
# Build image and start the container
docker compose up
```
## With Uvicorn
```
pip install -r requirements.txt
redis-server
```
```
# Run the following in a new terminal
cd app/
uvicorn main:app --reload
```
