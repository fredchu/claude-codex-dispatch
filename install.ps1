# claude-codex-dispatch installer (PowerShell)
# Usage: iwr -useb https://raw.githubusercontent.com/fredchu/claude-codex-dispatch/main/install.ps1 | iex

$ErrorActionPreference = "Stop"

$Repo = "https://github.com/fredchu/claude-codex-dispatch.git"
$SkillName = "claude-codex-dispatch"
$SkillsDir = if ($env:CLAUDE_SKILLS_DIR) { $env:CLAUDE_SKILLS_DIR } else { Join-Path $env:USERPROFILE ".claude\skills" }
$Target = Join-Path $SkillsDir $SkillName

Write-Host ""
Write-Host "📦 Installing $SkillName"
Write-Host "   Target: $Target"
Write-Host ""

function Check-Dep($cmd, $hint) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Host "⚠️  $cmd not found in PATH. $hint"
        return $false
    }
    return $true
}

$DepsOk = $true
if (-not (Check-Dep "codex" "Install: https://github.com/openai/codex")) { $DepsOk = $false }

# Python: try py first, then python (don't use Check-Dep — we want quiet probing)
$HasPy = Get-Command py -ErrorAction SilentlyContinue
$HasPython = Get-Command python -ErrorAction SilentlyContinue
if (-not ($HasPy -or $HasPython)) {
    Write-Host "⚠️  py / python not found in PATH. Install Python 3."
    $DepsOk = $false
}

if (-not (Check-Dep "git" "Required to clone the repo.")) {
    Write-Host "❌ git is required, aborting."
    exit 1
}

if (-not (Test-Path $SkillsDir)) {
    Write-Host "📁 Creating $SkillsDir"
    New-Item -ItemType Directory -Force -Path $SkillsDir | Out-Null
}

if (Test-Path $Target) {
    Write-Host "ℹ️  Already installed at $Target"
    Write-Host "   To update: cd $Target; git pull"
    Write-Host ""
    exit 0
}

Write-Host "⬇️  Cloning $Repo"
git clone --depth 1 $Repo $Target

Write-Host ""
Write-Host "🔍 Smoke test:"
$LauncherCmd = Join-Path $Target "bin\codex-dispatch.cmd"
& cmd /c "`"$LauncherCmd`" --help" 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Launcher runs."
} else {
    Write-Host "   ⚠️  Launcher failed --help; inspect $Target"
}

Write-Host ""
Write-Host "✅ Installed $SkillName"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Restart Claude Code (or run /reload-plugins) to pick up the skill"
Write-Host "  2. Read SKILL.md for the contract:"
Write-Host "     $Target\SKILL.md"
Write-Host "  3. Try the worker example:"
Write-Host "     Get-Content $Target\examples\worker.md"
Write-Host ""

if (-not $DepsOk) {
    Write-Host "⚠️  Some optional deps missing — install them before first dispatch."
    Write-Host ""
}
