[CmdletBinding()]
param(
    [string]$RepoUrl = "https://github.com/r2gul4r/selfdex.git",
    [string]$Branch = "main",
    [string]$InstallRoot = $(Join-Path $HOME "selfdex"),
    [string]$Python = "",
    [switch]$DryRun,
    [switch]$SkipPluginInstall,
    [switch]$SkipDoctor
)

$ErrorActionPreference = "Stop"

function Write-SelfdexStep {
    param([string]$Message)
    Write-Host "[selfdex] $Message"
}

function Resolve-RequiredCommand {
    param(
        [string[]]$Names,
        [string]$Purpose
    )

    foreach ($Name in $Names) {
        $Command = Get-Command $Name -ErrorAction SilentlyContinue
        if ($null -ne $Command) {
            return $Command.Source
        }
    }

    throw "Missing required command for $Purpose. Tried: $($Names -join ', ')"
}

function Resolve-PythonCommand {
    if ($Python -ne "") {
        return ,@($Python)
    }

    foreach ($Name in @("python", "python3")) {
        $Command = Get-Command $Name -ErrorAction SilentlyContinue
        if ($null -ne $Command) {
            return ,@($Command.Source)
        }
    }

    $BundledPython = Join-Path $HOME ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    if (Test-Path $BundledPython) {
        return ,@($BundledPython)
    }

    $PyLauncher = Get-Command "py" -ErrorAction SilentlyContinue
    if ($null -ne $PyLauncher) {
        return ,@($PyLauncher.Source, "-3")
    }

    throw "Missing Python. Install Python 3 or pass -Python <path>."
}

function Invoke-Git {
    param([string[]]$Arguments)
    & $Git @Arguments
}

$InstallRoot = [System.IO.Path]::GetFullPath($InstallRoot)

Write-SelfdexStep "repo: $RepoUrl"
Write-SelfdexStep "branch: $Branch"
Write-SelfdexStep "install root: $InstallRoot"

if ($DryRun) {
    Write-SelfdexStep "dry run: no clone, update, or plugin install will run"
    Write-SelfdexStep "would clone Selfdex if missing, or pull --ff-only if already present"
    if (-not $SkipPluginInstall) {
        Write-SelfdexStep "would run scripts/install_selfdex_plugin.py --root `"$InstallRoot`" --yes --force"
    }
    if ((-not $SkipPluginInstall) -and (-not $SkipDoctor)) {
        Write-SelfdexStep "would run scripts/check_selfdex_setup.py --root `"$InstallRoot`" --format markdown"
    }
    exit 0
}

$Git = Resolve-RequiredCommand -Names @("git") -Purpose "cloning or updating Selfdex"
$PythonCommand = Resolve-PythonCommand
$PythonExe = $PythonCommand[0]
$PythonArgs = @()
if ($PythonCommand.Count -gt 1) {
    $PythonArgs = $PythonCommand[1..($PythonCommand.Count - 1)]
}

$GitDir = Join-Path $InstallRoot ".git"
if (Test-Path $GitDir) {
    Write-SelfdexStep "updating existing checkout"
    Invoke-Git @("-C", $InstallRoot, "fetch", "origin", $Branch)
    Invoke-Git @("-C", $InstallRoot, "checkout", $Branch)
    Invoke-Git @("-C", $InstallRoot, "pull", "--ff-only", "origin", $Branch)
} elseif (Test-Path $InstallRoot) {
    $Existing = Get-ChildItem -LiteralPath $InstallRoot -Force -ErrorAction SilentlyContinue
    if ($Existing.Count -gt 0) {
        throw "Install root exists but is not an empty Selfdex git checkout: $InstallRoot"
    }
    Write-SelfdexStep "cloning into existing empty directory"
    Invoke-Git @("clone", "--branch", $Branch, $RepoUrl, $InstallRoot)
} else {
    Write-SelfdexStep "cloning Selfdex"
    Invoke-Git @("clone", "--branch", $Branch, $RepoUrl, $InstallRoot)
}

if ($SkipPluginInstall) {
    Write-SelfdexStep "skipped plugin install"
    exit 0
}

$Installer = Join-Path $InstallRoot "scripts\install_selfdex_plugin.py"
if (-not (Test-Path $Installer)) {
    throw "Plugin installer was not found after checkout: $Installer"
}

Write-SelfdexStep "installing @selfdex plugin"
& $PythonExe @PythonArgs $Installer --root $InstallRoot --yes --force --format markdown

if (-not $SkipDoctor) {
    $Doctor = Join-Path $InstallRoot "scripts\check_selfdex_setup.py"
    if (-not (Test-Path $Doctor)) {
        throw "Setup doctor was not found after checkout: $Doctor"
    }
    Write-SelfdexStep "checking setup"
    & $PythonExe @PythonArgs $Doctor --root $InstallRoot --format markdown
}

Write-SelfdexStep "done. Restart or refresh Codex plugin discovery, then call @selfdex from a target project session."
