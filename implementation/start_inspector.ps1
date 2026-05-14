$Root = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$Python = if (Test-Path $VenvPython) { $VenvPython } else { (Get-Command python).Source }
$env:NPM_CONFIG_CACHE = Join-Path $Root ".npm-cache"

Write-Host "Starting MCP Inspector..."
Write-Host "Server command: $Python $PSScriptRoot\mcp_server.py"
npx -y @modelcontextprotocol/inspector $Python "$PSScriptRoot\mcp_server.py"
