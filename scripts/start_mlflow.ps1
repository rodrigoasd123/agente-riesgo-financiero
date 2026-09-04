$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "No se encontro .venv. Ejecuta primero la instalacion del proyecto."
}

Set-Location -LiteralPath $projectRoot
& $python -m mlflow ui `
    --backend-store-uri sqlite:///mlflow.db `
    --host 127.0.0.1 `
    --port 5000
