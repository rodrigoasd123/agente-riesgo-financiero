"""Configuracion hermetica de la suite: sin red ni trazas MLflow."""

import os


os.environ["GEMINI_API_KEY"] = ""
os.environ["GMAIL_CLIENT_ID"] = ""
os.environ["GMAIL_CLIENT_SECRET"] = ""
os.environ["GMAIL_REFRESH_TOKEN"] = ""
os.environ["GMAIL_ACCOUNT_EMAIL"] = ""
os.environ["MLFLOW_ENABLED"] = "false"
