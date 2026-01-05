import os

class Config:
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME = os.getenv("DB_NAME")

    RPC_PORT = int(os.getenv("RPC_PORT"))

    VALIDATION_HOST = os.getenv("VALIDATION_HOST")
    VALIDATION_PORT = int(os.getenv("VALIDATION_PORT"))