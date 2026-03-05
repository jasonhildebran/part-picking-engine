from fastapi import FastAPI

app = FastAPI(title="Part Picker API")

@app.get("/health")
def health_check():
    return {"status": "200 OK"}
