[CmdletBinding()]
param(
    [string]$SshUser = "dohyun",
    [string]$OutputDirectory = "docs/evidence/infrastructure/raw/2026-07-22-vm-inventory"
)

$ErrorActionPreference = "Stop"
$nodes = @(
    @{ Name = "mesh-cp-01"; Address = "192.168.200.10" },
    @{ Name = "mesh-worker-01"; Address = "192.168.200.11" },
    @{ Name = "mesh-worker-02"; Address = "192.168.200.12" }
)
$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
$collector = Join-Path $PSScriptRoot "collect-node-evidence.sh"
$targetDirectory = Join-Path $repositoryRoot $OutputDirectory
New-Item -ItemType Directory -Force -Path $targetDirectory | Out-Null

foreach ($node in $nodes) {
    Write-Host "Collecting $($node.Name) from $($node.Address)"
    $collectorSource = (Get-Content -Raw -Encoding UTF8 $collector) -replace "`r`n", "`n"
    $output = $collectorSource | ssh `
        -o BatchMode=yes `
        -o ConnectTimeout=10 `
        -o StrictHostKeyChecking=accept-new `
        "$SshUser@$($node.Address)" "tr -d '\r' | bash -s"
    if ($LASTEXITCODE -ne 0) {
        throw "Evidence collection failed for $($node.Name)"
    }
    $output | Set-Content -Encoding UTF8 (Join-Path $targetDirectory "$($node.Name).txt")
}

Write-Host "Saved node evidence to $targetDirectory"
Write-Host "Reboot all nodes, wait for Ready, and run this command again with a new output directory to prove persistence."
