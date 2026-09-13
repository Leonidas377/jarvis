# ==========================================================================
# J.A.R.V.I.S. Gateway Entry Point
# Delegates to modular server.main application
# ==========================================================================

from server.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.main:app", host="127.0.0.1", port=8000, reload=True)
