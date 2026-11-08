# Replace a LimitBuddy installation with its verified staged copy after NOVA has closed.
# Private data is moved (keeping its current-user permissions), never copied. The folder path
# stays the same, so hooks, the Start at sign-in entry and the limitbuddy command stay valid.
param(
    [Parameter(Mandatory)][string]$Root,
    [Parameter(Mandatory)][string]$Staged,
    [int]$WaitPid = 0,
    [switch]$StartHost,
    [string]$Log = (Join-Path ([IO.Path]::GetTempPath()) 'limitbuddy-update.log')
)
$ErrorActionPreference = 'Stop'
$log = $Log
function Note([string]$Message) { Add-Content -LiteralPath $log -Value ((Get-Date -Format s) + ' ' + $Message) }
function Retry([scriptblock]$Action) {
    # Hooks may briefly hold a file in the folder; never give up on the first sharing violation.
    for ($attempt = 1; ; $attempt++) {
        try { & $Action; return } catch { if ($attempt -ge 30) { throw }; Start-Sleep -Milliseconds 500 }
    }
}
$private = @('.env', 'tools\aim_host.json', 'tools\aim_host.status.json', 'tools\aim_host.log',
             'tools\aim_host.log.1', 'tools\activity', 'tools\companions', 'tools\permission-endpoint.json')
$patterns = @('aim_host.invalid-*.json', 'permission-trust*')
function Move-Private([string]$From, [string]$To) {
    $names = @($private)
    foreach ($pattern in $patterns) {
        Get-ChildItem -LiteralPath (Join-Path $From 'tools') -Filter $pattern -Force -ErrorAction SilentlyContinue |
            ForEach-Object { $names += 'tools\' + $_.Name }
    }
    foreach ($name in $names) {
        $source = Join-Path $From $name
        if (-not (Test-Path -LiteralPath $source)) { continue }
        $target = Join-Path $To $name
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
        if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target -Recurse -Force }
        Retry { Move-Item -LiteralPath $source -Destination $target }
    }
}

$Root = [IO.Path]::GetFullPath($Root).TrimEnd('\')
$Staged = [IO.Path]::GetFullPath($Staged).TrimEnd('\')
$previous = $Root + '.previous'
$moved = $false; $retired = $false
try {
    if ($Staged -ne ($Root + '.next')) { throw 'Unexpected staged folder' }
    if (-not (Test-Path -LiteralPath (Join-Path $Staged '.limitbuddy-staged'))) { throw 'Staged update is missing' }
    if ($WaitPid -gt 0) { Wait-Process -Id $WaitPid -Timeout 300 -ErrorAction SilentlyContinue }
    if (Test-Path -LiteralPath $previous) { Retry { Remove-Item -LiteralPath $previous -Recurse -Force } }
    Move-Private $Root $Staged; $moved = $true
    Retry { Rename-Item -LiteralPath $Root -NewName (Split-Path -Leaf $previous) }; $retired = $true
    Retry { Rename-Item -LiteralPath $Staged -NewName (Split-Path -Leaf $Root) }
    Remove-Item -LiteralPath (Join-Path $Root '.limitbuddy-staged') -Force
    Note ('Updated ' + $Root)
} catch {
    Note ('Update failed: ' + $_.Exception.Message)
    # Put everything back where it was; the previous version keeps working.
    if ($retired -and -not (Test-Path -LiteralPath $Root)) { Rename-Item -LiteralPath $previous -NewName (Split-Path -Leaf $Root) }
    if ($moved) { Move-Private $Staged $Root }
}
if ($StartHost) {
    Start-Process -FilePath (Join-Path $Root 'runtime\pythonw.exe') -WorkingDirectory $Root -WindowStyle Hidden `
        -ArgumentList @(('"' + (Join-Path $Root 'tools\aim_control.py') + '"'), '--start-host')
}
