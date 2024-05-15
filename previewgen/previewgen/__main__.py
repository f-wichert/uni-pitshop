import uvicorn  # type: ignore

# this is only meant for development

if __name__ == "__main__":
    uvicorn.run(
        "previewgen.main:app",
        host="127.0.0.1",
        port=6472,
        reload=True,
        log_level="debug",
        debug=True,
    )
