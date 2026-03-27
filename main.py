# main.py

from fastapi import FastAPI
from database import initialize_database  # Import your database initialization function

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await initialize_database()  # Call to initialize the database

@app.get("/")
def read_root():
    return {"Hello": "World"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)