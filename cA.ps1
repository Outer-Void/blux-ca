param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

if (-not $Args -or $Args.Count -eq 0) {
    Write-Output "Usage: .\cA.ps1 <command> [args...]"
    Write-Output "Example: .\cA.ps1 run --goal examples/goal_hello.json --out out/"
    exit 0
}

$python = Get-Command py -ErrorAction SilentlyContinue
if ($null -ne $python) {
    $pythonCmd = @("py", "-3")
} else {
    $pythonCmd = @("python")
}

if (-not (Test-Path ".venv")) {
    & $pythonCmd -m venv .venv
}

. .\.venv\Scripts\Activate.ps1

& $pythonCmd -m pip install -e ".[dev]"

& $pythonCmd -m blux_ca @Args
