$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

if (-not $Args -or $Args.Count -eq 0) {
    Write-Output "Usage: .\cA.ps1 <command> [args...]"
    Write-Output "Examples:"
    Write-Output "  .\cA.ps1 run --goal examples/goal_hello.json --out out/"
    Write-Output "  .\cA.ps1 accept --fixtures examples --out out/"
    exit 0
}

$pythonCmd = @("python")
$pyLauncher = Get-Command py -ErrorAction SilentlyContinue
if ($null -ne $pyLauncher) {
    & py -3.11 -V *> $null
    if ($LASTEXITCODE -eq 0) {
        $pythonCmd = @("py", "-3.11")
    } else {
        $pythonCmd = @("py", "-3")
    }
}

if (-not (Test-Path ".venv")) {
    & $pythonCmd -m venv .venv
}

. .\.venv\Scripts\Activate.ps1

python -m pip install -e ".[dev]"
python -m blux_ca @Args
