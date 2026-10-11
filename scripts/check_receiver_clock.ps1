param(
    [string]$Executable,
    [string]$ReceiverHome = (Join-Path $env:USERPROFILE 'ToneSentryData'),
    [switch]$NoPause
)
$ErrorActionPreference = 'Stop'
try {
    if (-not $Executable) {
        Add-Type -AssemblyName System.Windows.Forms
        $picker = New-Object System.Windows.Forms.OpenFileDialog
        $picker.Title = 'Select the Tone Sentry EXE used on this laptop'
        $picker.Filter = 'Windows application (*.exe)|*.exe'
        if ($picker.ShowDialog() -ne 'OK') { exit 0 }
        $Executable = $picker.FileName
        $picker.Dispose()
    }
    $Executable = (Resolve-Path -LiteralPath $Executable).Path
    $checkFolder = Join-Path $env:TEMP ('Tone Sentry clock check ' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $checkFolder | Out-Null
    $reportPath = Join-Path $checkFolder 'packaged-check.json'
    $before = [DateTimeOffset]::UtcNow
    # The existing self-test creates its own profile, synthetic audio and no destinations.
    $process = Start-Process -FilePath $Executable -ArgumentList @('--self-test', ('"' + $reportPath + '"')) -WindowStyle Hidden -PassThru
    if (-not $process.WaitForExit(120000)) {
        throw 'The isolated diagnostic has not finished after two minutes. The live receiver was not touched. The diagnostic process has been left open.'
    }
    $after = [DateTimeOffset]::UtcNow
    if (-not (Test-Path -LiteralPath $reportPath)) { throw 'The selected EXE did not create a diagnostic report. Select Tone Sentry 0.8.8.' }
    $check = Get-Content -LiteralPath $reportPath -Raw | ConvertFrom-Json
    if (-not $check.success) { throw ('Isolated application check failed: ' + $check.error) }
    $rows = @()
    function Read-RecordingTimes($folder, $label, $limit) {
        if (-not (Test-Path -LiteralPath $folder)) { return }
        Get-ChildItem -LiteralPath $folder -Filter '*.json' -File |
            Sort-Object LastWriteTimeUtc -Descending | Select-Object -First $limit | ForEach-Object {
                try {
                    $data = Get-Content -LiteralPath $_.FullName -Raw | ConvertFrom-Json
                    if ($null -eq $data.start -or $null -eq $data.end) { return }
                    $start = [DateTimeOffset]::FromUnixTimeMilliseconds([long]([double]$data.start * 1000))
                    $end = [DateTimeOffset]::FromUnixTimeMilliseconds([long]([double]$data.end * 1000))
                    [pscustomobject]@{
                        source = $label
                        filename = $_.Name
                        synthetic = $data.synthetic
                        stored_start_unix = $data.start
                        stored_start_local = $start.ToLocalTime().ToString('yyyy-MM-dd HH:mm:ss zzz')
                        stored_end_local = $end.ToLocalTime().ToString('yyyy-MM-dd HH:mm:ss zzz')
                        json_last_write_local = $_.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss')
                        file_write_minus_stored_end_seconds = [math]::Round(($_.LastWriteTimeUtc - $end.UtcDateTime).TotalSeconds, 3)
                        test_start_minus_windows_launch_seconds = $(if ($label -eq 'isolated test') { [math]::Round(($start - $before).TotalSeconds, 3) } else { $null })
                    }
                } catch { Write-Warning ('Could not inspect one recording: ' + $_.Exception.Message) }
            }
    }
    $rows += @(Read-RecordingTimes (Join-Path $check.data_home 'audio') 'isolated test' 5)
    $rows += @(Read-RecordingTimes (Join-Path $ReceiverHome 'audio') 'existing receiver' 3)
    $result = [ordered]@{
        application_version = $check.version
        executable_sha256 = (Get-FileHash -LiteralPath $Executable -Algorithm SHA256).Hash
        windows_local = $after.ToLocalTime().ToString('yyyy-MM-dd HH:mm:ss zzz')
        windows_utc = $after.ToString('yyyy-MM-dd HH:mm:ss')
        windows_zone = (Get-TimeZone).Id
        test_launch_unix = $before.ToUnixTimeSeconds()
        test_finish_unix = $after.ToUnixTimeSeconds()
        isolated_test_success = $check.success
        recordings = $rows
        note = 'Synthetic replay advances faster than real time; a few seconds difference is expected. File write times are clues only: copying or later edits can change them. No receiver settings or existing recordings were modified.'
    }
    $text = $result | ConvertTo-Json -Depth 6
    $summary = Join-Path $checkFolder 'clock-summary.json'
    $text | Set-Content -LiteralPath $summary -Encoding UTF8
    Write-Output $text
    Write-Output "`nSaved report: $summary"
} catch {
    Write-Output ('Clock check could not complete: ' + $_.Exception.Message)
} finally {
    if (-not $NoPause) { Read-Host 'Copy the output to the support chat. Press Enter to close' | Out-Null }
}
