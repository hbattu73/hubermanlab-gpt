# Running Locally
## With AWS SAM
```
# Build image
sam build --use-container
# Deploy locally
sam local invoke
```
## With Uvicorn
```
cd app/
pip install -r requirements.txt
uvicorn main:app --reload
```
