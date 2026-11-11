# SignageCast – Schnellstart unter Windows mit Docker Desktop (seit 0.44) / quick start on Windows with Docker Desktop
#
# In PowerShell (kein Administrator nötig / no administrator needed):
#   irm https://raw.githubusercontent.com/thefrozn/signagecast/main/windows/schnellstart.ps1 | iex
#
# Legt %USERPROFILE%\SignageCast an (compose.yaml + .env), lädt das Image und startet den Container.
# Erneut ausführen = Update; Einstellungen und Daten bleiben im Docker-Volume "signagecast".
# Eigene IP vorgeben (z. B. bei mehreren Netzwerkkarten): $env:SC_HOST_IP = "10.0.0.20" vor dem Befehl setzen.

$Quelle = 'https://raw.githubusercontent.com/thefrozn/signagecast/main/windows'
$Ordner = Join-Path $env:USERPROFILE 'SignageCast'

function Sag([string]$Text) { Write-Host "SignageCast: $Text" }
function Fehler([string]$Text) { Write-Host "SignageCast: $Text" -ForegroundColor Red }

function Start-SignageCast {
    # 1. Docker Desktop
    if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64') {
        Fehler 'Windows auf ARM wird nicht unterstützt (Image nur für x86/amd64). / Windows on ARM is not supported.'
        return
    }
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Fehler 'Docker Desktop fehlt / Docker Desktop is missing:'
        Write-Host '  winget install -e --id Docker.DockerDesktop'
        Write-Host '  Danach neu anmelden, Docker Desktop einmal starten und diesen Befehl wiederholen.'
        Write-Host '  Then sign in again, start Docker Desktop once and run this command again.'
        return
    }
    docker info *> $null
    if ($LASTEXITCODE -ne 0) {
        $exe = Join-Path $env:ProgramFiles 'Docker\Docker\Docker Desktop.exe'
        if (Test-Path $exe) { Sag 'starte Docker Desktop … / starting Docker Desktop …'; Start-Process $exe }
        for ($i = 0; $i -lt 60; $i++) {
            Start-Sleep -Seconds 3
            docker info *> $null
            if ($LASTEXITCODE -eq 0) { break }
        }
        if ($LASTEXITCODE -ne 0) { Fehler 'Docker Desktop antwortet nicht – bitte starten und wiederholen. / Docker Desktop does not answer.'; return }
    }
    if ((docker info --format '{{.OSType}}' 2> $null) -ne 'linux') {
        Fehler 'Docker Desktop läuft mit Windows-Containern – im Tray-Menü "Switch to Linux containers" wählen. / Switch to Linux containers.'
        return
    }

    # 2. IP im Heimnetz und Zeitzone
    $ip = $env:SC_HOST_IP
    if (-not $ip) {
        $netz = Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway -and $_.NetAdapter.Status -eq 'Up' } | Select-Object -First 1
        if ($netz) { $ip = @($netz.IPv4Address)[0].IPAddress }
    }
    if (-not $ip) { Fehler 'IP im Heimnetz nicht gefunden – $env:SC_HOST_IP setzen und wiederholen. / Home network IP not found – set $env:SC_HOST_IP.'; return }
    $tz = 'Europe/Berlin'
    try {   # .NET 6+ (PowerShell 7); Windows PowerShell 5.1 kann es nicht -> Europe/Berlin, in der Verwaltung änderbar
        $iana = $null
        if ([TimeZoneInfo]::TryConvertWindowsIdToIanaId([TimeZoneInfo]::Local.Id, [ref]$iana)) { $tz = $iana }
    } catch { }

    # 3. Dateien
    New-Item -ItemType Directory -Force -Path $Ordner | Out-Null
    try {
        Invoke-WebRequest -UseBasicParsing -Uri "$Quelle/compose.yaml" -OutFile (Join-Path $Ordner 'compose.yaml')
    } catch {
        Fehler "compose.yaml nicht geladen / not downloaded: $($_.Exception.Message)"; return
    }
    # .env ohne BOM (Windows PowerShell schreibt bei utf8 ein BOM, das Compose stört)
    [IO.File]::WriteAllText((Join-Path $Ordner '.env'), "SC_HOST_IP=$ip`nTZ=$tz`n", [Text.Encoding]::ASCII)

    # 4. Laden und starten (bei einem Update: neues Image, Container neu, Volume bleibt)
    Push-Location $Ordner
    try {
        Sag 'lade das Image (beim ersten Mal einige Minuten) … / pulling the image …'
        docker compose -p signagecast pull
        if ($LASTEXITCODE -ne 0) { Fehler 'Image nicht geladen – Internet? / Image not pulled.'; return }
        docker compose -p signagecast up -d
        if ($LASTEXITCODE -ne 0) {
            Fehler 'Start fehlgeschlagen. Gibt es schon einen Container "signagecast" von Hand? Dann: docker rm -f signagecast (Daten im Volume bleiben).'
            return
        }
    } finally { Pop-Location }

    # 5. Startpasswort aus dem Protokoll (steht dort, bis es in der Verwaltung geändert ist)
    $pw = $null
    for ($i = 0; $i -lt 30 -and -not $pw; $i++) {
        Start-Sleep -Seconds 2
        $zeile = docker logs signagecast 2> $null | Select-String -Pattern 'initial admin password: (\S+)' | Select-Object -Last 1
        if ($zeile) { $pw = $zeile.Matches[0].Groups[1].Value }
    }

    Write-Host ''
    Sag "läuft / running ($ip, $tz)"
    Write-Host "  Verwaltung / admin:   http://localhost:19090   (im Heimnetz / home network: http://${ip}:19090)"
    if ($pw) { Write-Host "  Startpasswort / initial password: $pw   – bitte ändern / please change it" }
    else { Write-Host '  Passwort: das bereits geänderte / password: the one you set' }
    Write-Host "  Fernseher / TV:       http://${ip}:8888/tv"
    Write-Host '  Fragt die Windows-Firewall nach, Zugriff im privaten Netzwerk erlauben. / Allow access on private networks.'
    Write-Host '  Docker Desktop → Settings → General → "Start Docker Desktop when you sign in" einschalten; Energiesparmodus aus.'
    Start-Process 'http://localhost:19090'
}

Start-SignageCast
