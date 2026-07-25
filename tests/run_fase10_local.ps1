[CmdletBinding()]
param(
    [switch]$SelfTest,
    [ValidateSet("All", "Descriptor", "Pytest", "Disconnect", "Reconnect")]
    [string]$FailureInjection = "All"
)

$ErrorActionPreference = "Stop"

$DevContainer = "studiamatch-dev"
$SentinelNetwork = "studiamatch-f9-local"
$SentinelOwnerLabel = "studiamatch.f10.sentinel-owner"
$MutexName = "Global\StudIAMatch-F9-F10-Isolation"
$MutexTimeoutSeconds = 15
$DockerTimeoutSeconds = 30
$DescriptorTimeoutSeconds = 120
$PytestTimeoutSeconds = 900
$script:DockerCommandExecutor = $null
if ($PSBoundParameters.ContainsKey("FailureInjection")) {
    $SelfTest = $true
}

function New-CommandResult {
    param(
        [int]$ExitCode,
        [string]$StdOut = "",
        [string]$StdErr = "",
        [bool]$TimedOut = $false
    )

    return [pscustomobject]@{
        ExitCode = $ExitCode
        StdOut = $StdOut
        StdErr = $StdErr
        TimedOut = $TimedOut
    }
}

function ConvertTo-NativeArgument {
    param([AllowEmptyString()][string]$Argument)

    if ($Argument.Length -eq 0) { return '""' }
    if ($Argument -notmatch '[\s"]') { return $Argument }

    $builder = New-Object System.Text.StringBuilder
    [void]$builder.Append('"')
    $backslashes = 0
    foreach ($character in $Argument.ToCharArray()) {
        if ($character -eq [char]92) {
            $backslashes++
            continue
        }
        if ($character -eq [char]34) {
            [void]$builder.Append(('\' * (($backslashes * 2) + 1)))
            [void]$builder.Append('"')
            $backslashes = 0
            continue
        }
        if ($backslashes -gt 0) {
            [void]$builder.Append(('\' * $backslashes))
            $backslashes = 0
        }
        [void]$builder.Append($character)
    }
    if ($backslashes -gt 0) {
        [void]$builder.Append(('\' * ($backslashes * 2)))
    }
    [void]$builder.Append('"')
    return $builder.ToString()
}

function Invoke-BoundedProcess {
    param(
        [Parameter(Mandatory = $true)][string]$FileName,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][int]$TimeoutSeconds
    )

    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $FileName
    $startInfo.Arguments = (($Arguments | ForEach-Object { ConvertTo-NativeArgument $_ }) -join " ")
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo
    try {
        if (-not $process.Start()) {
            return New-CommandResult -ExitCode 1
        }
        $stdoutTask = $process.StandardOutput.ReadToEndAsync()
        $stderrTask = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
            try { $process.Kill() } catch { }
            $process.WaitForExit()
            return New-CommandResult -ExitCode 124 -StdOut $stdoutTask.Result -StdErr $stderrTask.Result -TimedOut $true
        }
        $process.WaitForExit()
        return New-CommandResult -ExitCode $process.ExitCode -StdOut $stdoutTask.Result -StdErr $stderrTask.Result
    }
    catch {
        return New-CommandResult -ExitCode 1
    }
    finally {
        $process.Dispose()
    }
}

function Invoke-DockerCommand {
    param(
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [int]$TimeoutSeconds = $DockerTimeoutSeconds
    )

    if ($null -ne $script:DockerCommandExecutor) {
        return & $script:DockerCommandExecutor $Arguments $TimeoutSeconds
    }
    return Invoke-BoundedProcess -FileName "docker" -Arguments $Arguments -TimeoutSeconds $TimeoutSeconds
}

function Invoke-DockerRequired {
    param(
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [int]$TimeoutSeconds = $DockerTimeoutSeconds
    )

    $result = Invoke-DockerCommand -Arguments $Arguments -TimeoutSeconds $TimeoutSeconds
    if ($result.ExitCode -ne 0) {
        throw "Bounded Docker orchestration failed"
    }
    return $result
}

function Invoke-DockerWithRetry {
    param(
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [int]$TimeoutSeconds = $DockerTimeoutSeconds,
        [int]$Attempts = 2
    )

    $lastResult = New-CommandResult -ExitCode 1
    for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
        $lastResult = Invoke-DockerCommand -Arguments $Arguments -TimeoutSeconds $TimeoutSeconds
        if ($lastResult.ExitCode -eq 0) { break }
    }
    return $lastResult
}

function New-RandomHex {
    $randomBytes = New-Object byte[] 16
    $randomGenerator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $randomGenerator.GetBytes($randomBytes)
    }
    finally {
        $randomGenerator.Dispose()
    }
    $randomSuffix = [System.BitConverter]::ToString($randomBytes).Replace("-", "").ToLowerInvariant()
    return $randomSuffix
}

function New-IsolationNetworkName {
    return "studiamatch-f10-isolation-$(New-RandomHex)"
}

function Get-ObjectPropertyValue {
    param(
        [AllowNull()][object]$Object,
        [Parameter(Mandatory = $true)][string]$Name
    )

    if ($null -eq $Object) { return $null }
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $null }
    return $property.Value
}

function Get-NetworkNames {
    $result = Invoke-DockerRequired -Arguments @("network", "ls", "--format", "{{.Name}}")
    return @(($result.StdOut -split "`r?`n") | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
}

function New-FaseIsolationSentinel {
    param([Parameter(Mandatory = $true)][string]$OwnerToken)

    $createResult = Invoke-DockerCommand -Arguments @(
        "network", "create", "--internal", "--label",
        "$SentinelOwnerLabel=$OwnerToken", $SentinelNetwork
    )
    $owned = $createResult.ExitCode -eq 0
    if (-not $owned) {
        return [pscustomobject]@{ Owned = $false; Success = $false }
    }

    $labelsResult = Invoke-DockerCommand -Arguments @(
        "network", "inspect", "--format", "{{json .Labels}}", $SentinelNetwork
    )
    $internalResult = Invoke-DockerCommand -Arguments @(
        "network", "inspect", "--format", "{{.Internal}}", $SentinelNetwork
    )
    $peersResult = Invoke-DockerCommand -Arguments @(
        "network", "inspect", "--format", "{{len .Containers}}", $SentinelNetwork
    )
    $success = $false
    if ($labelsResult.ExitCode -eq 0 -and $internalResult.ExitCode -eq 0 -and
        $peersResult.ExitCode -eq 0 -and -not [string]::IsNullOrWhiteSpace($labelsResult.StdOut)) {
        $labels = $labelsResult.StdOut.Trim() | ConvertFrom-Json
        $observedOwner = [string](Get-ObjectPropertyValue -Object $labels -Name $SentinelOwnerLabel)
        $success = ($observedOwner -ceq $OwnerToken -and
            $internalResult.StdOut.Trim() -eq "true" -and $peersResult.StdOut.Trim() -eq "0")
    }
    return [pscustomobject]@{ Owned = $owned; Success = $success }
}

function Test-FaseIsolationSentinel {
    param([Parameter(Mandatory = $true)][string]$OwnerToken)

    $labelsResult = Invoke-DockerCommand -Arguments @(
        "network", "inspect", "--format", "{{json .Labels}}", $SentinelNetwork
    )
    $internalResult = Invoke-DockerCommand -Arguments @(
        "network", "inspect", "--format", "{{.Internal}}", $SentinelNetwork
    )
    $peersResult = Invoke-DockerCommand -Arguments @(
        "network", "inspect", "--format", "{{len .Containers}}", $SentinelNetwork
    )
    if ($labelsResult.ExitCode -ne 0 -or $internalResult.ExitCode -ne 0 -or
        $peersResult.ExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($labelsResult.StdOut)) {
        return $false
    }
    $labels = $labelsResult.StdOut.Trim() | ConvertFrom-Json
    $observedOwner = [string](Get-ObjectPropertyValue -Object $labels -Name $SentinelOwnerLabel)
    return ($observedOwner -ceq $OwnerToken -and
        $internalResult.StdOut.Trim() -eq "true" -and $peersResult.StdOut.Trim() -eq "0")
}

function Remove-FaseIsolationSentinel {
    param(
        [Parameter(Mandatory = $true)][string]$OwnerToken,
        [Parameter(Mandatory = $true)][bool]$Owned
    )

    if (-not $Owned) { return $false }
    try {
        if (@(Get-NetworkNames) -notcontains $SentinelNetwork) { return $true }
        $labelsResult = Invoke-DockerCommand -Arguments @(
            "network", "inspect", "--format", "{{json .Labels}}", $SentinelNetwork
        )
        if ($labelsResult.ExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($labelsResult.StdOut)) {
            return $true
        }
        $labels = $labelsResult.StdOut.Trim() | ConvertFrom-Json
        $observedOwner = [string](Get-ObjectPropertyValue -Object $labels -Name $SentinelOwnerLabel)
        if ($observedOwner -cne $OwnerToken) { return $true }
        $removeResult = Invoke-DockerWithRetry -Arguments @("network", "rm", $SentinelNetwork)
        if ($removeResult.ExitCode -ne 0) { return $true }
        return (@(Get-NetworkNames) -contains $SentinelNetwork)
    }
    catch {
        return $true
    }
}

function Get-RunningContainerNames {
    $result = Invoke-DockerRequired -Arguments @("container", "ls", "--format", "{{.Names}}")
    return @(($result.StdOut -split "`r?`n") | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
}

function Assert-NoActiveFaseIsolation {
    $networkNames = @(Get-NetworkNames)
    $containerNames = @(Get-RunningContainerNames)
    $activeNetwork = @($networkNames | Where-Object {
        $_ -eq "studiamatch-f9-local" -or $_ -like "studiamatch-f10-isolation-*"
    })
    $activeContainer = @($containerNames | Where-Object {
        $_ -eq "studiamatch-f9-postgres" -or $_ -like "studiamatch-f10-*"
    })
    if ($activeNetwork.Count -gt 0 -or $activeContainer.Count -gt 0) {
        throw "FASE-09 or FASE-10 isolation is already active"
    }
}

function Get-EndpointConfigs {
    param([Parameter(Mandatory = $true)][string]$Container)

    $result = Invoke-DockerRequired -Arguments @(
        "inspect", "--format", "{{json .NetworkSettings.Networks}}", $Container
    )
    if ([string]::IsNullOrWhiteSpace($result.StdOut)) {
        throw "Docker endpoint inspection returned no data"
    }
    $networkObject = $result.StdOut.Trim() | ConvertFrom-Json
    $configs = @()
    foreach ($networkProperty in @($networkObject.PSObject.Properties)) {
        $endpoint = $networkProperty.Value
        $ipam = Get-ObjectPropertyValue -Object $endpoint -Name "IPAMConfig"
        $aliases = @((Get-ObjectPropertyValue -Object $endpoint -Name "Aliases") |
            Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) })
        $linkLocal = @((Get-ObjectPropertyValue -Object $ipam -Name "LinkLocalIPs") |
            Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) })

        $driverOptions = @()
        $driverObject = Get-ObjectPropertyValue -Object $endpoint -Name "DriverOpts"
        if ($null -ne $driverObject) {
            foreach ($driverProperty in @($driverObject.PSObject.Properties)) {
                $driverOptions += [pscustomobject]@{
                    Key = [string]$driverProperty.Name
                    Value = [string]$driverProperty.Value
                }
            }
        }
        $staticIPv4 = [string](Get-ObjectPropertyValue -Object $ipam -Name "IPv4Address")
        $staticIPv6 = [string](Get-ObjectPropertyValue -Object $ipam -Name "IPv6Address")
        $staticMacConfigured = @($driverOptions | Where-Object {
            $_.Key -match '(?i)mac.?address'
        }).Count -gt 0

        $gatewayProperty = $endpoint.PSObject.Properties["GwPriority"]
        if ($null -eq $gatewayProperty) {
            $gatewayProperty = $endpoint.PSObject.Properties["GatewayPriority"]
        }
        $gatewayExposed = $null -ne $gatewayProperty
        $gatewayPriority = if ($gatewayExposed) { [int]$gatewayProperty.Value } else { 0 }

        $configs += [pscustomobject]@{
            Name = [string]$networkProperty.Name
            Aliases = @($aliases)
            IPv4Address = $staticIPv4
            IPv6Address = $staticIPv6
            LinkLocalIPs = @($linkLocal)
            DriverOpts = @($driverOptions)
            GatewayPriorityExposed = $gatewayExposed
            GatewayPriority = $gatewayPriority
            StaticRuntimeIPv4 = if (-not [string]::IsNullOrWhiteSpace($staticIPv4)) {
                [string](Get-ObjectPropertyValue -Object $endpoint -Name "IPAddress")
            } else { "" }
            StaticRuntimeIPv6 = if (-not [string]::IsNullOrWhiteSpace($staticIPv6)) {
                [string](Get-ObjectPropertyValue -Object $endpoint -Name "GlobalIPv6Address")
            } else { "" }
            StaticRuntimeMac = if ($staticMacConfigured) {
                [string](Get-ObjectPropertyValue -Object $endpoint -Name "MacAddress")
            } else { "" }
        }
    }
    return @($configs)
}

function ConvertTo-NormalizedEndpointJson {
    param([Parameter(Mandatory = $true)][object]$Endpoint)

    $normalizedDriverOptions = @($Endpoint.DriverOpts |
        Sort-Object Key, Value |
        ForEach-Object { [ordered]@{ Key = $_.Key; Value = $_.Value } })
    $normalized = [ordered]@{
        Name = $Endpoint.Name
        Aliases = @($Endpoint.Aliases | Sort-Object -Unique)
        IPv4Address = $Endpoint.IPv4Address
        IPv6Address = $Endpoint.IPv6Address
        LinkLocalIPs = @($Endpoint.LinkLocalIPs | Sort-Object -Unique)
        DriverOpts = $normalizedDriverOptions
        GatewayPriorityExposed = [bool]$Endpoint.GatewayPriorityExposed
        GatewayPriority = if ($Endpoint.GatewayPriorityExposed) { [int]$Endpoint.GatewayPriority } else { $null }
        StaticRuntimeIPv4 = $Endpoint.StaticRuntimeIPv4
        StaticRuntimeIPv6 = $Endpoint.StaticRuntimeIPv6
        StaticRuntimeMac = $Endpoint.StaticRuntimeMac
    }
    return ($normalized | ConvertTo-Json -Compress -Depth 6)
}

function Test-EndpointSetsEqual {
    param(
        [Parameter(Mandatory = $true)][object[]]$Expected,
        [Parameter(Mandatory = $true)][object[]]$Actual
    )

    if ($Expected.Count -ne $Actual.Count) { return $false }
    foreach ($expectedEndpoint in $Expected) {
        $actualEndpoint = @($Actual | Where-Object { $_.Name -eq $expectedEndpoint.Name })
        if ($actualEndpoint.Count -ne 1) { return $false }
        if ((ConvertTo-NormalizedEndpointJson $expectedEndpoint) -cne
            (ConvertTo-NormalizedEndpointJson $actualEndpoint[0])) {
            return $false
        }
    }
    return $true
}

function Get-NetworkConnectCapabilities {
    $result = Invoke-DockerRequired -Arguments @("network", "connect", "--help")
    return @{
        Alias = $result.StdOut.Contains("--alias")
        IPv4 = $result.StdOut.Contains("--ip ")
        IPv6 = $result.StdOut.Contains("--ip6")
        LinkLocal = $result.StdOut.Contains("--link-local-ip")
        DriverOpt = $result.StdOut.Contains("--driver-opt")
        GatewayPriority = $result.StdOut.Contains("--gw-priority")
    }
}

function Assert-EndpointRestorationSupported {
    param(
        [Parameter(Mandatory = $true)][object[]]$Endpoints,
        [Parameter(Mandatory = $true)][hashtable]$Capabilities
    )

    foreach ($endpoint in $Endpoints) {
        if ($endpoint.Aliases.Count -gt 0 -and -not $Capabilities.Alias) {
            throw "Docker cannot restore network aliases"
        }
        if (-not [string]::IsNullOrWhiteSpace($endpoint.IPv4Address) -and -not $Capabilities.IPv4) {
            throw "Docker cannot restore static IPv4 IPAM"
        }
        if (-not [string]::IsNullOrWhiteSpace($endpoint.IPv6Address) -and -not $Capabilities.IPv6) {
            throw "Docker cannot restore static IPv6 IPAM"
        }
        if ($endpoint.LinkLocalIPs.Count -gt 0 -and -not $Capabilities.LinkLocal) {
            throw "Docker cannot restore link-local IPAM"
        }
        if ($endpoint.DriverOpts.Count -gt 0 -and -not $Capabilities.DriverOpt) {
            throw "Docker cannot restore endpoint driver options"
        }
        if ($endpoint.GatewayPriorityExposed -and $endpoint.GatewayPriority -ne 0 -and
            -not $Capabilities.GatewayPriority) {
            throw "Docker cannot restore endpoint gateway priority"
        }
    }
}

function Connect-OriginalEndpoint {
    param(
        [Parameter(Mandatory = $true)][object]$Endpoint,
        [Parameter(Mandatory = $true)][hashtable]$Capabilities,
        [Parameter(Mandatory = $true)][string]$Container
    )

    $arguments = @("network", "connect")
    foreach ($alias in $Endpoint.Aliases) {
        if (-not $Capabilities.Alias) { return $false }
        $arguments += @("--alias", [string]$alias)
    }
    if (-not [string]::IsNullOrWhiteSpace($Endpoint.IPv4Address)) {
        if (-not $Capabilities.IPv4) { return $false }
        $arguments += @("--ip", $Endpoint.IPv4Address)
    }
    if (-not [string]::IsNullOrWhiteSpace($Endpoint.IPv6Address)) {
        if (-not $Capabilities.IPv6) { return $false }
        $arguments += @("--ip6", $Endpoint.IPv6Address)
    }
    foreach ($linkLocalIp in $Endpoint.LinkLocalIPs) {
        if (-not $Capabilities.LinkLocal) { return $false }
        $arguments += @("--link-local-ip", [string]$linkLocalIp)
    }
    foreach ($driverOption in $Endpoint.DriverOpts) {
        if (-not $Capabilities.DriverOpt) { return $false }
        $arguments += @("--driver-opt", "$($driverOption.Key)=$($driverOption.Value)")
    }
    if ($Endpoint.GatewayPriorityExposed -and $Endpoint.GatewayPriority -ne 0) {
        if (-not $Capabilities.GatewayPriority) { return $false }
        $arguments += @("--gw-priority", [string]$Endpoint.GatewayPriority)
    }
    $arguments += @($Endpoint.Name, $Container)
    $result = Invoke-DockerWithRetry -Arguments $arguments
    return $result.ExitCode -eq 0
}

function Test-IsolatedNetwork {
    param(
        [Parameter(Mandatory = $true)][string]$Network,
        [Parameter(Mandatory = $true)][string]$ExpectedContainerId
    )

    $result = Invoke-DockerCommand -Arguments @(
        "network", "inspect", "--format", "{{json .Containers}}", $Network
    )
    if ($result.ExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($result.StdOut)) {
        return $false
    }
    $peers = @((($result.StdOut.Trim() | ConvertFrom-Json).PSObject.Properties))
    return ($peers.Count -eq 1 -and $peers[0].Name -eq $ExpectedContainerId)
}

function Invoke-TopologyCleanup {
    param(
        [Parameter(Mandatory = $true)][string]$Container,
        [Parameter(Mandatory = $true)][string]$IsolationNetwork,
        [Parameter(Mandatory = $true)][object[]]$OriginalEndpoints,
        [Parameter(Mandatory = $true)][hashtable]$ConnectCapabilities,
        [Parameter(Mandatory = $true)][bool]$NetworkCreationAuthorized
    )

    $cleanupFailed = $false
    if (-not $NetworkCreationAuthorized) { return $false }

    try {
        $currentEndpoints = @(Get-EndpointConfigs -Container $Container)
        if (@($currentEndpoints.Name) -contains $IsolationNetwork) {
            $disconnectResult = Invoke-DockerWithRetry -Arguments @(
                "network", "disconnect", "--force", $IsolationNetwork, $Container
            )
            if ($disconnectResult.ExitCode -ne 0) { $cleanupFailed = $true }
        }
    }
    catch {
        $cleanupFailed = $true
    }

    foreach ($originalEndpoint in $OriginalEndpoints) {
        try {
            $currentEndpoints = @(Get-EndpointConfigs -Container $Container)
            if (@($currentEndpoints.Name) -notcontains $originalEndpoint.Name) {
                if (-not (Connect-OriginalEndpoint -Endpoint $originalEndpoint -Capabilities $ConnectCapabilities -Container $Container)) {
                    $cleanupFailed = $true
                }
            }
        }
        catch {
            $cleanupFailed = $true
        }
    }

    try {
        $networkNames = @(Get-NetworkNames)
        if ($networkNames -contains $IsolationNetwork) {
            $removeResult = Invoke-DockerWithRetry -Arguments @("network", "rm", $IsolationNetwork)
            if ($removeResult.ExitCode -ne 0) { $cleanupFailed = $true }
        }
        if (@(Get-NetworkNames) -contains $IsolationNetwork) { $cleanupFailed = $true }
    }
    catch {
        $cleanupFailed = $true
    }

    try {
        $restoredEndpoints = @(Get-EndpointConfigs -Container $Container)
        if (-not (Test-EndpointSetsEqual -Expected $OriginalEndpoints -Actual $restoredEndpoints)) {
            $cleanupFailed = $true
        }
    }
    catch {
        $cleanupFailed = $true
    }
    return $cleanupFailed
}

function Invoke-CleanupSelfTest {
    $scenarios = if ($FailureInjection -eq "All") {
        @("Descriptor", "Pytest", "Disconnect", "Reconnect")
    }
    else {
        @($FailureInjection)
    }

    foreach ($scenario in $scenarios) {
        $ownerToken = "selftestowner000000000000000000000001"
        $isolationNetwork = "studiamatch-f10-isolation-selftest"
        $state = @{
            SentinelExists = $true
            SentinelOwner = "concurrent-f9-owner"
            IsolationNetworkExists = $false
            IsolationConnected = $false
            OriginalConnected = $true
        }
        $attempts = @{}
        $script:DockerCommandExecutor = {
            param([string[]]$Arguments, [int]$TimeoutSeconds)
            $operation = $Arguments -join " "
            if (-not $attempts.ContainsKey($operation)) { $attempts[$operation] = 0 }
            $attempts[$operation]++

            if ($Arguments[0] -eq "network" -and $Arguments[1] -eq "ls") {
                $names = @("bridge")
                if ($state.SentinelExists) { $names += $SentinelNetwork }
                if ($state.IsolationNetworkExists) { $names += $isolationNetwork }
                return New-CommandResult -ExitCode 0 -StdOut (($names -join "`n") + "`n")
            }
            if ($Arguments[0] -eq "container" -and $Arguments[1] -eq "ls") {
                return New-CommandResult -ExitCode 0 -StdOut ""
            }
            if ($Arguments[0] -eq "network" -and $Arguments[1] -eq "create" -and
                $Arguments[-1] -eq $SentinelNetwork) {
                if ($state.SentinelExists) { return New-CommandResult -ExitCode 1 }
                $labelIndex = [Array]::IndexOf($Arguments, "--label")
                $labelParts = $Arguments[$labelIndex + 1] -split "=", 2
                $state.SentinelExists = $true
                $state.SentinelOwner = $labelParts[1]
                return New-CommandResult -ExitCode 0 -StdOut "self-test-sentinel-id`n"
            }
            if ($Arguments[0] -eq "network" -and $Arguments[1] -eq "inspect" -and
                $Arguments[-1] -eq $SentinelNetwork) {
                if (-not $state.SentinelExists) { return New-CommandResult -ExitCode 1 }
                $formatIndex = [Array]::IndexOf($Arguments, "--format")
                $format = $Arguments[$formatIndex + 1]
                if ($format -eq "{{json .Labels}}") {
                    $labels = [ordered]@{ $SentinelOwnerLabel = $state.SentinelOwner }
                    return New-CommandResult -ExitCode 0 -StdOut (($labels | ConvertTo-Json -Compress) + "`n")
                }
                if ($format -eq "{{.Internal}}") { return New-CommandResult -ExitCode 0 -StdOut "true`n" }
                if ($format -eq "{{len .Containers}}") { return New-CommandResult -ExitCode 0 -StdOut "0`n" }
            }
            if ($Arguments[0] -eq "inspect" -and $Arguments[-1] -eq "self-test-dev") {
                $networkObject = [ordered]@{}
                if ($state.OriginalConnected) {
                    $networkObject["bridge"] = [ordered]@{
                        IPAMConfig = [ordered]@{}
                        Aliases = @()
                        DriverOpts = [ordered]@{}
                        GwPriority = 0
                        IPAddress = "172.17.0.4"
                        GlobalIPv6Address = ""
                        MacAddress = "dynamic-mac-ignored"
                    }
                }
                if ($state.IsolationConnected) {
                    $networkObject[$isolationNetwork] = [ordered]@{
                        IPAMConfig = [ordered]@{}
                        Aliases = @()
                        DriverOpts = [ordered]@{}
                        GwPriority = 0
                        IPAddress = "172.30.0.2"
                        GlobalIPv6Address = ""
                        MacAddress = "dynamic-isolation-mac"
                    }
                }
                return New-CommandResult -ExitCode 0 -StdOut (($networkObject | ConvertTo-Json -Compress -Depth 6) + "`n")
            }
            if ($Arguments[0] -eq "network" -and $Arguments[1] -eq "disconnect") {
                if ($scenario -eq "Disconnect" -and $attempts[$operation] -eq 1) {
                    return New-CommandResult -ExitCode 1
                }
                $state.IsolationConnected = $false
                return New-CommandResult -ExitCode 0
            }
            if ($Arguments[0] -eq "network" -and $Arguments[1] -eq "connect") {
                if ($scenario -eq "Reconnect" -and $attempts[$operation] -eq 1) {
                    return New-CommandResult -ExitCode 1
                }
                $state.OriginalConnected = $true
                return New-CommandResult -ExitCode 0
            }
            if ($Arguments[0] -eq "network" -and $Arguments[1] -eq "rm") {
                if ($Arguments[-1] -eq $SentinelNetwork) {
                    $state.SentinelExists = $false
                }
                if ($Arguments[-1] -eq $isolationNetwork) {
                    $state.IsolationNetworkExists = $false
                }
                return New-CommandResult -ExitCode 0
            }
            return New-CommandResult -ExitCode 1
        }.GetNewClosure()

        $concurrentRejected = $false
        try { Assert-NoActiveFaseIsolation } catch { $concurrentRejected = $true }
        if (-not $concurrentRejected) { throw "concurrent-start rejection self-test failed" }

        $state.SentinelExists = $false
        $state.SentinelOwner = ""
        $sentinelResult = New-FaseIsolationSentinel -OwnerToken $ownerToken
        if (-not $sentinelResult.Owned -or -not $sentinelResult.Success -or
            -not (Test-FaseIsolationSentinel -OwnerToken $ownerToken)) {
            throw "sentinel creation self-test failed"
        }
        $state.IsolationNetworkExists = $true
        $state.IsolationConnected = $true
        $state.OriginalConnected = $false

        $expectedEndpoint = [pscustomobject]@{
            Name = "bridge"
            Aliases = @()
            IPv4Address = ""
            IPv6Address = ""
            LinkLocalIPs = @()
            DriverOpts = @()
            GatewayPriorityExposed = $true
            GatewayPriority = 0
            StaticRuntimeIPv4 = ""
            StaticRuntimeIPv6 = ""
            StaticRuntimeMac = ""
        }
        $capabilities = @{
            Alias = $true
            IPv4 = $true
            IPv6 = $true
            LinkLocal = $true
            DriverOpt = $true
            GatewayPriority = $true
        }
        $cleanupReached = $false
        try {
            if ($scenario -eq "Descriptor") { throw "descriptor_failure" }
            if ($scenario -eq "Pytest") { throw "pytest_failure" }
        }
        catch { }
        finally {
            $cleanupReached = $true
            $topologyCleanupFailed = Invoke-TopologyCleanup `
                -Container "self-test-dev" `
                -IsolationNetwork $isolationNetwork `
                -OriginalEndpoints @($expectedEndpoint) `
                -ConnectCapabilities $capabilities `
                -NetworkCreationAuthorized $true
            $sentinelCleanupFailed = Remove-FaseIsolationSentinel `
                -OwnerToken $ownerToken -Owned $sentinelResult.Owned
        }
        if (-not $cleanupReached -or $topologyCleanupFailed -or $sentinelCleanupFailed -or
            $state.IsolationConnected -or -not $state.OriginalConnected -or
            $state.IsolationNetworkExists -or $state.SentinelExists) {
            throw "production cleanup path self-test failed for $scenario"
        }
    }
    $script:DockerCommandExecutor = $null
}

if ($SelfTest) {
    try {
        Invoke-CleanupSelfTest
        Write-Output "FASE-10 local promotion contract self-test: PASS"
        exit 0
    }
    catch {
        $script:DockerCommandExecutor = $null
        Write-Output "FASE-10 local promotion contract self-test: FAIL"
        exit 1
    }
}

$evidenceExitCode = 1
$succeeded = $false
$networkCreationAuthorized = $false
$originalEndpoints = @()
$connectCapabilities = @{}
$NetworkName = $null
$sentinelOwnerToken = $null
$sentinelOwned = $false
$isolationMutex = $null
$mutexAcquired = $false

try {
    $isolationMutex = New-Object System.Threading.Mutex($false, $MutexName)
    try {
        $mutexAcquired = $isolationMutex.WaitOne([TimeSpan]::FromSeconds($MutexTimeoutSeconds))
    }
    catch [System.Threading.AbandonedMutexException] {
        $mutexAcquired = $true
    }
    if (-not $mutexAcquired) {
        throw "FASE isolation mutex acquisition timed out"
    }

    Assert-NoActiveFaseIsolation
    $sentinelOwnerToken = New-RandomHex
    $sentinelResult = New-FaseIsolationSentinel -OwnerToken $sentinelOwnerToken
    $sentinelOwned = [bool]$sentinelResult.Owned
    if (-not $sentinelResult.Success) {
        throw "Could not atomically own the FASE-09 isolation sentinel"
    }
    $NetworkName = New-IsolationNetworkName

    $runningResult = Invoke-DockerRequired -Arguments @("inspect", "--format", "{{.State.Running}}", $DevContainer)
    if ($runningResult.StdOut.Trim() -ne "true") { throw "Development container is not running" }
    $identityResult = Invoke-DockerRequired -Arguments @("inspect", "--format", "{{.Id}}", $DevContainer)
    $devContainerId = $identityResult.StdOut.Trim()
    if ([string]::IsNullOrWhiteSpace($devContainerId)) { throw "Development container identity is unavailable" }

    $venvResult = Invoke-DockerCommand -Arguments @(
        "exec", "--workdir", "/app", $DevContainer,
        "env", "-i", "HOME=/tmp", "PATH=/usr/local/bin:/usr/bin:/bin",
        "/usr/bin/test", "-d", "/tmp/f10qa"
    )
    if ($venvResult.ExitCode -ne 0) { throw "FASE-10 virtual environment is not installed" }
    $pythonResult = Invoke-DockerCommand -Arguments @(
        "exec", "--workdir", "/app", $DevContainer,
        "env", "-i", "HOME=/tmp", "PATH=/usr/local/bin:/usr/bin:/bin",
        "/usr/bin/test", "-x", "/tmp/f10qa/bin/python"
    )
    if ($pythonResult.ExitCode -ne 0) { throw "FASE-10 Python executable is not installed" }

    $originalEndpoints = @(Get-EndpointConfigs -Container $DevContainer)
    $connectCapabilities = Get-NetworkConnectCapabilities
    Assert-EndpointRestorationSupported -Endpoints $originalEndpoints -Capabilities $connectCapabilities
    if (@(Get-NetworkNames) -contains $NetworkName) { throw "Generated FASE-10 network already exists" }

    $networkCreationAuthorized = $true
    $createResult = Invoke-DockerRequired -Arguments @("network", "create", "--internal", $NetworkName)
    $emptyResult = Invoke-DockerRequired -Arguments @(
        "network", "inspect", "--format", "{{len .Containers}}", $NetworkName
    )
    if ($emptyResult.StdOut.Trim() -ne "0") { throw "FASE-10 network was not created empty" }

    $connectResult = Invoke-DockerRequired -Arguments @("network", "connect", $NetworkName, $DevContainer)
    if (-not (Test-IsolatedNetwork -Network $NetworkName -ExpectedContainerId $devContainerId)) {
        throw "FASE-10 network has unexpected peers"
    }
    foreach ($originalEndpoint in $originalEndpoints) {
        $disconnectResult = Invoke-DockerRequired -Arguments @(
            "network", "disconnect", "--force", $originalEndpoint.Name, $DevContainer
        )
    }
    $isolatedEndpoints = @(Get-EndpointConfigs -Container $DevContainer)
    if ($isolatedEndpoints.Count -ne 1 -or $isolatedEndpoints[0].Name -ne $NetworkName -or
        -not (Test-IsolatedNetwork -Network $NetworkName -ExpectedContainerId $devContainerId)) {
        throw "Development container network isolation failed"
    }
    if (-not (Test-FaseIsolationSentinel -OwnerToken $sentinelOwnerToken)) {
        throw "FASE isolation sentinel ownership was lost"
    }

    $descriptorResult = Invoke-DockerCommand -TimeoutSeconds ($DescriptorTimeoutSeconds + 30) -Arguments @(
        "exec", "--workdir", "/app", $DevContainer,
        "env", "-i", "HOME=/tmp", "PATH=/tmp/f10qa/bin:/usr/local/bin:/usr/bin:/bin", "PYTHONPATH=/app",
        "timeout", "--signal=TERM", "--kill-after=10s", "${DescriptorTimeoutSeconds}s",
        "/tmp/f10qa/bin/python", "scripts/maintenance/db_migrate.py", "--env", "free",
        "--promotion-contract", "db/manifests/fase10_promotion_contract.json", "--validate-only"
    )
    if ($descriptorResult.ExitCode -ne 0) {
        $evidenceExitCode = $descriptorResult.ExitCode
        throw "FASE-10 descriptor validation failed"
    }
    if (-not (Test-IsolatedNetwork -Network $NetworkName -ExpectedContainerId $devContainerId)) {
        throw "FASE-10 network has unexpected peers"
    }
    if (-not (Test-FaseIsolationSentinel -OwnerToken $sentinelOwnerToken)) {
        throw "FASE isolation sentinel ownership was lost"
    }

    $pytestResult = Invoke-DockerCommand -TimeoutSeconds ($PytestTimeoutSeconds + 30) -Arguments @(
        "exec", "--workdir", "/app", $DevContainer,
        "env", "-i", "HOME=/tmp", "CI=true", "PATH=/tmp/f10qa/bin:/usr/local/bin:/usr/bin:/bin", "PYTHONPATH=/app",
        "timeout", "--signal=TERM", "--kill-after=10s", "${PytestTimeoutSeconds}s",
        "/tmp/f10qa/bin/python", "-m", "pytest", "-q",
        "tests/test_fase06_db_as_code.py", "tests/test_fase07_g1b.py",
        "tests/test_fase08_db.py", "tests/test_fase08_workers.py",
        "tests/test_fase09_db.py", "tests/test_fase09_workers.py",
        "tests/test_fase10_promotion_contract.py", "tests/test_supabase_credentials_contract.py"
    )
    if ($pytestResult.ExitCode -ne 0) {
        $evidenceExitCode = $pytestResult.ExitCode
        throw "FASE-10 test suite failed"
    }
    if (-not (Test-IsolatedNetwork -Network $NetworkName -ExpectedContainerId $devContainerId)) {
        throw "FASE-10 network has unexpected peers"
    }
    if (-not (Test-FaseIsolationSentinel -OwnerToken $sentinelOwnerToken)) {
        throw "FASE isolation sentinel ownership was lost"
    }

    $evidenceExitCode = 0
    $succeeded = $true
}
catch {
    $succeeded = $false
}
finally {
    $cleanupFailed = $false
    if ($networkCreationAuthorized) {
        $cleanupFailed = Invoke-TopologyCleanup `
            -Container $DevContainer `
            -IsolationNetwork $NetworkName `
            -OriginalEndpoints $originalEndpoints `
            -ConnectCapabilities $connectCapabilities `
            -NetworkCreationAuthorized $networkCreationAuthorized
    }
    if (Remove-FaseIsolationSentinel -OwnerToken $sentinelOwnerToken -Owned $sentinelOwned) {
        $cleanupFailed = $true
    }
    if ($mutexAcquired -and $null -ne $isolationMutex) {
        try { $isolationMutex.ReleaseMutex() } catch { $cleanupFailed = $true }
    }
    if ($null -ne $isolationMutex) {
        try { $isolationMutex.Dispose() } catch { $cleanupFailed = $true }
    }
    if ($cleanupFailed) {
        $succeeded = $false
        if ($evidenceExitCode -eq 0) { $evidenceExitCode = 1 }
    }
}

if ($succeeded) {
    Write-Output "FASE-10 local promotion contract: PASS"
    exit 0
}
Write-Output "FASE-10 local promotion contract: FAIL"
exit $evidenceExitCode
