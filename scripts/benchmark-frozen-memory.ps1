param([string]$OutputDirectory = ('frozen-' + (Get-Date -Format 'yyyyMMdd-HHmmss')))
$ErrorActionPreference = 'Stop'
if ($OutputDirectory -notmatch '^[a-zA-Z0-9_-]+$') { throw 'OutputDirectory must be a simple directory name.' }
$repoRoot = Split-Path -Parent $PSScriptRoot
$reportsRoot = Join-Path $repoRoot '.comparison/reports'
$inputsRoot = Join-Path $reportsRoot 'corrected-2026-11-11/benchmark-inputs'
if (-not (Test-Path -LiteralPath (Join-Path $inputsRoot 'prices.json'))) { throw 'The preserved benchmark input snapshot is required.' }
if (Test-Path -LiteralPath (Join-Path $reportsRoot $OutputDirectory)) { throw 'Use a new output directory to preserve previous evidence.' }
$composeFile = Join-Path $repoRoot 'comparison/compose.frozen-memory.yaml'
try {
    docker compose -f $composeFile up -d --force-recreate
    if ($LASTEXITCODE -ne 0) { throw 'Could not start benchmark containers.' }
    foreach ($implementation in @('python', 'rust')) {
        $targetContainer = "backtest-memory-$implementation-api-1"
        docker run --rm --network backtest-compare_default --pid "container:$targetContainer" --cgroupns host `
            --mount "type=bind,source=$repoRoot/comparison,target=/scripts,readonly" `
            --mount "type=bind,source=$reportsRoot,target=/reports" `
            python:3.15-slim-trixie python /scripts/benchmark-memory.py --server $implementation `
            --samples-root /reports/corrected-2026-11-11/benchmark-inputs --output "/reports/$OutputDirectory" `
            --readiness-path /health --repeats 10
        if ($LASTEXITCODE -ne 0) { throw "$implementation benchmark failed." }
    }
} finally {
    docker compose -f $composeFile down
}
Write-Output "Saved to $(Join-Path $reportsRoot $OutputDirectory)"
