"""Crea un .env local seguro sin imprimir secretos."""

from __future__ import annotations

import argparse
import secrets
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / ".env.example"
TARGET = ROOT / ".env"
PLACEHOLDER = "REEMPLAZAR_POR_UN_SECRETO_ALEATORIO_DE_32_CARACTERES"


def build_env() -> str:
    template = EXAMPLE.read_text(encoding="utf-8")
    return template.replace(PLACEHOLDER, secrets.token_urlsafe(48))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="sobrescribe un .env existente")
    args = parser.parse_args()

    if TARGET.exists() and not args.force:
        raise SystemExit(".env ya existe; usa --force solo si deseas reemplazarlo")

    TARGET.write_text(build_env(), encoding="utf-8")
    print(".env creado. Pega tu clave solo en GEMINI_API_KEY y no lo subas a Git.")


if __name__ == "__main__":
    main()
