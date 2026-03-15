# Run all NMA validation scripts and generate JSON artifacts
# Usage: powershell -ExecutionPolicy Bypass -File R_validation/run_all.ps1
$ErrorActionPreference = "Stop"
Write-Host "=== NMA Canonical Validation ===" -ForegroundColor Cyan

Write-Host "Running frequentist validation (netmeta)..." -ForegroundColor Yellow
Rscript R_validation/validate_nma_netmeta.R
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED" -ForegroundColor Red; exit 1 }
Write-Host "  -> frequentist_reference.json generated" -ForegroundColor Green

Write-Host "Running Bayesian validation (gemtc + JAGS)..." -ForegroundColor Yellow
Rscript R_validation/validate_nma_bayesian.R
if ($LASTEXITCODE -ne 0) { Write-Host "WARNING: JAGS may not be installed" -ForegroundColor Yellow }

Write-Host "Done. JSON artifacts in R_validation/" -ForegroundColor Green
