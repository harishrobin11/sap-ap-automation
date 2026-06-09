from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, you can replace "*" with your specific ".streamlit.app" URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
