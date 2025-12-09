# The Sovereign Desktop - Quick Activation Script
# Run this to activate the virtual environment and start working

$venvPath = Join-Path $PSScriptRoot "sovereign_agent"
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"

if (Test-Path $activateScript) {
    . $activateScript
    Write-Host ""
    Write-Host "  🏛️ The Sovereign Desktop environment activated!" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Commands:" -ForegroundColor White
    Write-Host "    python main.py          - Start in text mode" -ForegroundColor Gray
    Write-Host "    python main.py --voice  - Start in voice mode" -ForegroundColor Gray
    Write-Host "    python main.py --debug  - Start with debug logging" -ForegroundColor Gray
    Write-Host "    deactivate              - Exit the virtual environment" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "  Virtual environment not found. Run setup_env.ps1 first." -ForegroundColor Red
}
