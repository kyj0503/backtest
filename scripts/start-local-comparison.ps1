$ErrorActionPreference = 'Stop'
$comparisonRoot = Split-Path -Parent $PSScriptRoot
$consoleRoot = Join-Path (Split-Path -Parent $comparisonRoot) 'backtest-console'
$snapshots = Join-Path $comparisonRoot '.comparison'
New-Item -ItemType Directory -Path $snapshots -Force | Out-Null

function Export-ComparisonSource {
    param([string]$Repository, [string]$Revision, [string]$Name, [string[]]$Paths)
    $destination = Join-Path $snapshots $Name
    $marker = Join-Path $destination 'COMPARISON_SOURCE_REVISION'
    if (Test-Path $destination) {
        if (!(Test-Path $marker) -or (Get-Content $marker -Raw).Trim() -ne $Revision) {
            throw "Existing comparison snapshot has an unexpected revision: $destination"
        }
        return
    }
    $archive = Join-Path $snapshots "$Name.tar"
    & git -C $Repository archive --format=tar "--output=$archive" $Revision @Paths
    if ($LASTEXITCODE -ne 0) { throw "git archive failed: $Name" }
    New-Item -ItemType Directory -Path $destination | Out-Null
    & tar -xf $archive -C $destination
    if ($LASTEXITCODE -ne 0) { throw "Source extraction failed: $Name" }
    Set-Content -LiteralPath $marker -Value $Revision -Encoding utf8
    Remove-Item -LiteralPath $archive
}

Export-ComparisonSource -Repository $comparisonRoot -Revision 'b7a284f81283db1a537d15a5b49cc892f7f039d7' -Name 'python' -Paths @('backtest_be_fast','database/schema.sql')
Export-ComparisonSource -Repository $consoleRoot -Revision '40931a59703b768c13c37071d3f7e41797a21ae9' -Name 'console-python' -Paths @()
& docker compose --project-directory $comparisonRoot -f (Join-Path $comparisonRoot 'compose.compare.yaml') up -d --build --wait --wait-timeout 180
if ($LASTEXITCODE -ne 0) { throw 'Comparison startup failed. Check docker compose logs.' }
Write-Output 'Python UI: http://localhost:5173/backtest | API: http://localhost:8000'
Write-Output 'Rust UI:   http://localhost:5174/backtest | API: http://localhost:8001'
