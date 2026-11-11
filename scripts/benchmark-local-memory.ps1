param(
    [ValidatePattern('^[a-zA-Z0-9_-]+$')]
    [string]$ReportDirectory = ('memory-' + (Get-Date -Format 'yyyyMMdd-HHmmss')),
    [ValidatePattern('^[a-zA-Z0-9_-]+$')]
    [string]$SamplesDirectory = 'scenarios'
)
$ErrorActionPreference = 'Stop'
$comparisonRoot = Split-Path -Parent $PSScriptRoot
$memoryCompose = Join-Path $comparisonRoot 'comparison/compose.memory.yaml'
$reportRoot = Join-Path $comparisonRoot '.comparison/reports'
$memoryScript = Join-Path $comparisonRoot 'comparison/benchmark-memory.py'
if (-not (Test-Path -LiteralPath (Join-Path $reportRoot "$SamplesDirectory/normal.json"))) {
    throw 'Run comparison/benchmark.py first to save the normal scenario inputs.'
}
if (Test-Path -LiteralPath (Join-Path $reportRoot $ReportDirectory)) {
    throw "Report directory already exists: $ReportDirectory. Choose a new name to preserve evidence."
}
try {
    docker compose -f $memoryCompose up -d --no-build
    if ($LASTEXITCODE -ne 0) { throw 'Temporary memory benchmark API startup failed.' }
    foreach ($implementation in @('python', 'rust')) {
        docker run --rm --name "backtest-memory-observer-$implementation" `
            "--pid=container:backtest-memory-$implementation-api-1" --cgroupns=host `
            --network backtest-compare_default `
            --mount "type=bind,source=$memoryScript,target=/memory.py,readonly" `
            --mount "type=bind,source=$reportRoot,target=/reports" `
            python:3.15-slim-trixie python -u /memory.py --server $implementation --output "/reports/$ReportDirectory" --samples-root "/reports/$SamplesDirectory"
        if ($LASTEXITCODE -ne 0) { throw "$implementation memory benchmark failed." }
    }
    Write-Output "Memory evidence: $(Join-Path $reportRoot $ReportDirectory)"
} finally {
    docker compose -f $memoryCompose down
}
