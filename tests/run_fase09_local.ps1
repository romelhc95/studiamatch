$ErrorActionPreference = "Stop"

$Image = "postgres:17-alpine@sha256:742f40ea20b9ff2ff31db5458d127452988a2164df9e17441e191f3b72252193"
$NetworkName = "studiamatch-f9-local"
$PostgresContainer = "studiamatch-f9-postgres"
$DevContainer = "studiamatch-dev"
$TestDatabaseUrl = "postgresql://postgres:postgres@studiamatch-f9-postgres:5432/studiamatch_f9"

$networkOwned = $false
$devConnected = $false
$containerMayExist = $false
$succeeded = $false
$failureReason = "unknown orchestration failure"
$originalNetworks = @()
$disconnectedNetworks = @()

function Invoke-DockerQuiet {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)
    & docker @Arguments *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker orchestration command failed"
    }
}

try {
    & docker image inspect $Image *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Pinned PostgreSQL image is not available locally"
    }

    $devRunning = & docker inspect --format "{{.State.Running}}" $DevContainer 2>$null
    if ($LASTEXITCODE -ne 0 -or $devRunning.Trim() -ne "true") {
        throw "Development container is not running"
    }
    $networkList = & docker inspect --format '{{range $name, $network := .NetworkSettings.Networks}}{{$name}} {{end}}' $DevContainer
    if ($LASTEXITCODE -ne 0) {
        throw "Could not inspect development container networks"
    }
    $originalNetworks = @($networkList.Trim().Split(" ") | Where-Object { $_ })

    & docker exec $DevContainer psql --version *> $null
    if ($LASTEXITCODE -ne 0) {
        Invoke-DockerQuiet @(
            "exec", $DevContainer,
            "env", "-i",
            "HOME=/tmp",
            "PATH=/usr/local/bin:/usr/bin:/bin",
            "bash", "-c",
            "apt-get update >/dev/null && apt-get install -y postgresql-client >/dev/null"
        )
    }

    $existingContainer = & docker container ls --all --quiet --filter "name=^/$PostgresContainer$"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not inspect existing FASE-09 containers"
    }
    if (-not [string]::IsNullOrWhiteSpace(($existingContainer -join ""))) {
        throw "FASE-09 PostgreSQL container already exists"
    }
    $existingNetwork = & docker network ls --quiet --filter "name=^$NetworkName$"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not inspect existing FASE-09 networks"
    }
    if (-not [string]::IsNullOrWhiteSpace(($existingNetwork -join ""))) {
        throw "FASE-09 internal network already exists"
    }

    Invoke-DockerQuiet @("network", "create", "--internal", $NetworkName)
    $networkOwned = $true
    Invoke-DockerQuiet @("network", "connect", $NetworkName, $DevContainer)
    $devConnected = $true
    foreach ($originalNetwork in $originalNetworks) {
        Invoke-DockerQuiet @(
            "network", "disconnect", "--force", $originalNetwork, $DevContainer
        )
        $disconnectedNetworks += $originalNetwork
    }

    $containerMayExist = $true
    Invoke-DockerQuiet @(
        "run", "--detach", "--pull=never",
        "--name", $PostgresContainer,
        "--network", $NetworkName,
        "--env", "POSTGRES_PASSWORD=postgres",
        "--env", "POSTGRES_DB=studiamatch_f9",
        "--health-cmd", "pg_isready -U postgres -d studiamatch_f9",
        "--health-interval", "1s",
        "--health-timeout", "3s",
        "--health-retries", "30",
        $Image
    )

    $healthy = $false
    for ($attempt = 0; $attempt -lt 45; $attempt++) {
        $health = & docker inspect --format "{{.State.Health.Status}}" $PostgresContainer 2>$null
        if ($LASTEXITCODE -eq 0 -and $health.Trim() -eq "healthy") {
            $healthy = $true
            break
        }
        Start-Sleep -Seconds 1
    }
    if (-not $healthy) {
        throw "Ephemeral PostgreSQL did not become healthy"
    }

    Invoke-DockerQuiet @(
        "exec", "--workdir", "/app", $DevContainer,
        "env", "-i",
        "HOME=/tmp",
        "CI=true",
        "PATH=/tmp/f9qa/bin:/usr/local/bin:/usr/bin:/bin",
        "PYTHONPATH=/app",
        "/tmp/f9qa/bin/python", "-m", "pytest", "-q",
        "tests/test_fase09_db.py", "tests/test_fase09_workers.py"
    )
    Invoke-DockerQuiet @(
        "exec", "--workdir", "/app", $DevContainer,
        "env", "-i",
        "HOME=/tmp",
        "PATH=/tmp/f9qa/bin:/usr/local/bin:/usr/bin:/bin",
        "PYTHONPATH=/app",
        "TEST_DATABASE_URL=$TestDatabaseUrl",
        "bash", "tests/sql/run_fase09_postgres.sh"
    )
    $succeeded = $true
}
catch {
    $succeeded = $false
    $failureReason = $_.Exception.Message
}
finally {
    if ($containerMayExist) {
        & docker rm --force $PostgresContainer *> $null
        if ($LASTEXITCODE -ne 0) { $succeeded = $false }
    }
    if ($devConnected) {
        & docker network disconnect --force $NetworkName $DevContainer *> $null
        if ($LASTEXITCODE -ne 0) { $succeeded = $false }
    }
    foreach ($originalNetwork in $disconnectedNetworks) {
        & docker network connect $originalNetwork $DevContainer *> $null
        if ($LASTEXITCODE -ne 0) { $succeeded = $false }
    }
    if ($networkOwned) {
        & docker network rm $NetworkName *> $null
        if ($LASTEXITCODE -ne 0) { $succeeded = $false }
    }
}

if ($succeeded) {
    Write-Output "FASE-09 local PostgreSQL 17 orchestration: PASS"
    exit 0
}
Write-Error "FASE-09 local PostgreSQL 17 orchestration: FAIL ($failureReason)" -ErrorAction Continue
exit 1
