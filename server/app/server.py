from fastapi import FastAPI
from fastapi.responses import FileResponse

app = FastAPI()

@app.get("/update")
async def send_update():
    return FileResponse("hello.txt", filename="hello.txt")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
