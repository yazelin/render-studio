import uvicorn

def main() -> None:
    uvicorn.run("render_studio.server:app", host="127.0.0.1", port=8098, reload=False)

if __name__ == "__main__":
    main()
