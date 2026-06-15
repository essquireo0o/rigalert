param([string]$Label = "Daily")

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$ConfigFile = "$env:USERPROFILE\Desktop\rigalert_config.json"
$cfg = Get-Content $ConfigFile -Raw | ConvertFrom-Json

$GmailUser = $cfg.gmail_user
$AppPwd    = $cfg.gmail_app_password -replace ' ', ''
$ToList    = ($cfg.alert_to_email -split '[,;]') | ForEach-Object { $_.Trim() } | Where-Object { $_ }
$Farm      = $cfg.farm_name
$Port      = [int]$cfg.miner_port
$Subnet    = $cfg.start_ip -replace '\.\d+$', ''
$Cred      = New-Object PSCredential($GmailUser, (ConvertTo-SecureString $AppPwd -AsPlainText -Force))

Write-Host ""
Write-Host "RigAlert Daily Report" -ForegroundColor Yellow
Write-Host "Farm   : $Farm" -ForegroundColor Gray
Write-Host "Subnet : $Subnet.1 - 254  Port $Port" -ForegroundColor Gray
Write-Host "From   : $GmailUser" -ForegroundColor Gray
Write-Host "To     : $($ToList -join ', ')" -ForegroundColor Gray
Write-Host ""

# ── Parallel TCP probe ────────────────────────────────────────────────────────
Write-Host "Scanning $Subnet.x on port $Port..." -ForegroundColor Cyan
$conns = @{}
1..254 | ForEach-Object {
    $ip  = "$Subnet.$_"
    $tcp = New-Object System.Net.Sockets.TcpClient
    $conns[$ip] = @{ Tcp = $tcp; Ar = $tcp.BeginConnect($ip, $Port, $null, $null) }
}
Start-Sleep -Milliseconds 1100

$alive = @()
foreach ($ip in $conns.Keys) {
    $e = $conns[$ip]
    if ($e.Ar.IsCompleted -and $e.Tcp.Connected) { $alive += $ip }
    try { $e.Tcp.Close() } catch {}
}
$alive = $alive | Sort-Object { [Version]$_ }
Write-Host "Found: $($alive.Count) miner(s)" -ForegroundColor Green

# ── Query CGMiner API ─────────────────────────────────────────────────────────
function Get-CGMiner($ip, $port, $cmd) {
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $ar  = $tcp.BeginConnect($ip, $port, $null, $null)
        if (-not $ar.AsyncWaitHandle.WaitOne(5000)) { $tcp.Close(); return $null }
        $tcp.EndConnect($ar)
        $ns  = $tcp.GetStream()
        $ns.ReadTimeout  = 6000
        $ns.WriteTimeout = 3000
        $b   = [Text.Encoding]::ASCII.GetBytes($cmd)
        $ns.Write($b, 0, $b.Length)
        $sb  = New-Object System.Text.StringBuilder
        $buf = New-Object byte[] 8192
        do {
            $n = $ns.Read($buf, 0, $buf.Length)
            if ($n -gt 0) { [void]$sb.Append([Text.Encoding]::ASCII.GetString($buf, 0, $n)) }
        } while ($n -eq $buf.Length -and $ns.DataAvailable)
        $tcp.Close()
        $raw = $sb.ToString().TrimEnd([char]0).Trim()
        if (-not $raw) { return $null }
        return $raw | ConvertFrom-Json
    } catch { return $null }
}

function Prop($obj, $name) {
    $p = $obj.PSObject.Properties[$name]
    if ($p) { return $p.Value } else { return $null }
}

$miners = @()
foreach ($ip in $alive) {
    Write-Host "  $ip" -NoNewline
    $sum  = Get-CGMiner $ip $Port '{"command":"summary"}'
    $pool = Get-CGMiner $ip $Port '{"command":"pools"}'

    if (-not $sum -or -not $sum.SUMMARY) {
        Write-Host "  (no API data)" -ForegroundColor DarkGray
        $miners += [PSCustomObject]@{
            IP=$ip; THS=0; Temp="-"; Fan="-"; Uptime="-"
            Accepted=0; HWPct=0.0; Status="offline"; Pool="-"
        }
        continue
    }

    $s    = $sum.SUMMARY[0]
    $mhs  = [double](Prop $s "MHS 5s")
    if ($mhs -eq 0) { $mhs = [double](Prop $s "MHS av") }
    $ths  = [math]::Round($mhs / 1000000.0, 2)
    $temp = [double](Prop $s "Temperature")
    $fi   = [int](Prop $s "Fan Speed In")
    $fo   = [int](Prop $s "Fan Speed Out")
    $hw   = [int](Prop $s "Hardware Errors")
    $acc  = [int](Prop $s "Accepted")
    $up   = [int](Prop $s "Elapsed")

    $hwPct  = if ($hw -gt 0 -and ($acc + $hw) -gt 0) { [math]::Round($hw/($acc+$hw)*100,2) } else { 0.0 }
    $fan    = if ($fi -gt 0 -and $fo -gt 0) { "$fi / $fo RPM" } elseif ($fi -gt 0) { "$fi RPM" } else { "-" }
    $upStr  = if ($up -gt 0) { $d=[int]($up/86400);$h=[int](($up%86400)/3600); if($d-gt 0){"${d}d ${h}h"}else{"${h}h"} } else { "-" }
    $tempStr= if ($temp -gt 0) { "$([int]$temp)C" } else { "-" }

    $poolUrl = "-"
    if ($pool -and $pool.POOLS) {
        $act = $pool.POOLS | Where-Object { (Prop $_ "Stratum Active") -eq $true } | Select-Object -First 1
        if (-not $act) { $act = $pool.POOLS | Select-Object -First 1 }
        if ($act) { $poolUrl = (Prop $act "URL") }
    }

    $status = if ($ths -le 0) { "offline" } elseif ($temp -ge 85 -or $hwPct -ge 1.0) { "warning" } else { "online" }
    $col    = if($status -eq "online"){"Green"}elseif($status -eq "warning"){"Yellow"}else{"Red"}

    Write-Host "  $ths TH/s  $tempStr  $status" -ForegroundColor $col
    $miners += [PSCustomObject]@{
        IP=$ip; THS=$ths; Temp=$tempStr; Fan=$fan; Uptime=$upStr
        Accepted=$acc; HWPct=$hwPct; Status=$status; Pool=$poolUrl
    }
}

# ── Build HTML ────────────────────────────────────────────────────────────────
$now     = Get-Date -Format "yyyy-MM-dd HH:mm"
$total   = $miners.Count
$online  = ($miners | Where-Object Status -eq "online").Count
$warning = ($miners | Where-Object Status -eq "warning").Count
$offline = ($miners | Where-Object Status -eq "offline").Count
$totThs  = [math]::Round(($miners | Measure-Object THS -Sum).Sum, 2)
$problems= $miners | Where-Object { $_.Status -ne "online" }

$cBG="#0d1117"; $cCC="#161b22"; $cBR="#30363d"
$cOR="#c8a94b"; $cGR="#3fb950"; $cYL="#d29922"; $cRD="#f85149"
$cTX="#e6edf3"; $cMT="#8b949e"

function Badge($st) {
    switch ($st) {
        "online"  { return "<span style='background:$cGR;color:#000;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;'>ONLINE</span>" }
        "warning" { return "<span style='background:$cYL;color:#000;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;'>WARNING</span>" }
        default   { return "<span style='background:$cRD;color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;'>OFFLINE</span>" }
    }
}

$issueRows = ($problems | ForEach-Object {
    $pool = ($_.Pool -replace 'stratum\+tcp://','') -replace '/.*',''
    "<tr style='border-bottom:1px solid $cBR;'>" +
    "<td style='padding:9px 10px;'>" + (Badge $_.Status) + "</td>" +
    "<td style='padding:9px 10px;color:$cTX;font-family:monospace;'>$($_.IP)</td>" +
    "<td style='padding:9px 10px;color:$cOR;font-weight:700;'>$($_.THS) TH/s</td>" +
    "<td style='padding:9px 10px;color:$cTX;'>$($_.Temp)</td>" +
    "<td style='padding:9px 10px;color:$cTX;'>$($_.Fan)</td>" +
    "<td style='padding:9px 10px;color:$cMT;font-size:11px;'>$pool</td>" +
    "</tr>"
}) -join ""

$issuesSec = ""
if ($problems.Count -gt 0) {
    $issuesSec = "<h2 style='color:$cRD;font-size:15px;margin:24px 0 10px;'>Issues ($($problems.Count))</h2>" +
    "<table width='100%' cellpadding='0' cellspacing='0' style='border-collapse:collapse;border:1px solid $cBR;font-size:13px;'>" +
    "<thead><tr style='background:$cCC;'>" +
    "<th style='padding:8px 10px;text-align:left;color:$cMT;font-size:11px;'>STATUS</th>" +
    "<th style='padding:8px 10px;text-align:left;color:$cMT;font-size:11px;'>IP</th>" +
    "<th style='padding:8px 10px;text-align:left;color:$cMT;font-size:11px;'>HASHRATE</th>" +
    "<th style='padding:8px 10px;text-align:left;color:$cMT;font-size:11px;'>TEMP</th>" +
    "<th style='padding:8px 10px;text-align:left;color:$cMT;font-size:11px;'>FAN</th>" +
    "<th style='padding:8px 10px;text-align:left;color:$cMT;font-size:11px;'>POOL</th>" +
    "</tr></thead><tbody style='background:$cBG;'>$issueRows</tbody></table>"
}

$sortedMiners = $miners | Sort-Object @{E={if($_.Status -eq "offline"){0}elseif($_.Status -eq "warning"){1}else{2}}}, IP
$allRows = ($sortedMiners | ForEach-Object {
    $hwC = if ($_.HWPct -ge 1.0) { $cRD } else { $cTX }
    "<tr style='border-bottom:1px solid $cBR;'>" +
    "<td style='padding:7px 9px;'>" + (Badge $_.Status) + "</td>" +
    "<td style='padding:7px 9px;color:$cTX;font-family:monospace;font-size:12px;'>$($_.IP)</td>" +
    "<td style='padding:7px 9px;color:$cOR;font-weight:700;'>$($_.THS) TH/s</td>" +
    "<td style='padding:7px 9px;color:$cTX;'>$($_.Temp)</td>" +
    "<td style='padding:7px 9px;color:$cTX;font-size:12px;'>$($_.Fan)</td>" +
    "<td style='padding:7px 9px;color:$cTX;'>$($_.Uptime)</td>" +
    "<td style='padding:7px 9px;color:$hwC;'>$($_.HWPct)%</td>" +
    "</tr>"
}) -join ""

$subj = "[$Farm] RigAlert $Label Report - $online/$total Online | $totThs TH/s"
if ($problems.Count -gt 0) { $subj += " | $($problems.Count) Issues" }

$html = "<!DOCTYPE html><html><head><meta charset='UTF-8'></head>" +
"<body style='margin:0;padding:0;background:$cBG;font-family:Arial,sans-serif;'>" +
"<table width='100%' cellpadding='0' cellspacing='0'><tr><td>" +
"<table width='640' cellpadding='0' cellspacing='0' align='center' style='margin:24px auto;'>" +
"<tr><td style='background:$cCC;border:1px solid $cBR;border-radius:10px;padding:28px;'>" +
"<div style='margin-bottom:20px;border-bottom:1px solid $cBR;padding-bottom:16px;'>" +
"<span style='font-size:20px;font-weight:700;color:$cOR;'>RigAlert by ING Mining</span>" +
"<span style='font-size:13px;color:$cMT;margin-left:10px;'>$Farm - $Label Report</span>" +
"<div style='color:$cMT;font-size:12px;margin-top:5px;'>$now</div>" +
"</div>" +
"<table width='100%' cellpadding='0' cellspacing='10' style='margin-bottom:20px;'><tr>" +
"<td width='25%'><div style='background:$cBG;border:1px solid $cBR;border-top:3px solid $cGR;border-radius:6px;padding:14px;text-align:center;'><div style='font-size:30px;font-weight:700;color:$cGR;'>$online</div><div style='color:$cMT;font-size:11px;font-weight:700;margin-top:4px;'>ONLINE</div></div></td>" +
"<td width='25%'><div style='background:$cBG;border:1px solid $cBR;border-top:3px solid $cRD;border-radius:6px;padding:14px;text-align:center;'><div style='font-size:30px;font-weight:700;color:$cRD;'>$offline</div><div style='color:$cMT;font-size:11px;font-weight:700;margin-top:4px;'>OFFLINE</div></div></td>" +
"<td width='25%'><div style='background:$cBG;border:1px solid $cBR;border-top:3px solid $cYL;border-radius:6px;padding:14px;text-align:center;'><div style='font-size:30px;font-weight:700;color:$cYL;'>$warning</div><div style='color:$cMT;font-size:11px;font-weight:700;margin-top:4px;'>WARNINGS</div></div></td>" +
"<td width='25%'><div style='background:$cBG;border:1px solid $cBR;border-top:3px solid $cOR;border-radius:6px;padding:14px;text-align:center;'><div style='font-size:30px;font-weight:700;color:$cOR;'>$totThs</div><div style='color:$cMT;font-size:11px;font-weight:700;margin-top:4px;'>TOTAL TH/s</div></div></td>" +
"</tr></table>" +
$issuesSec +
"<h2 style='color:$cTX;font-size:15px;margin:24px 0 10px;'>All Miners ($total)</h2>" +
"<table width='100%' cellpadding='0' cellspacing='0' style='border-collapse:collapse;border:1px solid $cBR;font-size:12px;'>" +
"<thead><tr style='background:$cBG;'>" +
"<th style='padding:8px 9px;text-align:left;color:$cMT;font-size:10px;font-weight:700;'>STATUS</th>" +
"<th style='padding:8px 9px;text-align:left;color:$cMT;font-size:10px;font-weight:700;'>IP</th>" +
"<th style='padding:8px 9px;text-align:left;color:$cMT;font-size:10px;font-weight:700;'>HASHRATE</th>" +
"<th style='padding:8px 9px;text-align:left;color:$cMT;font-size:10px;font-weight:700;'>TEMP</th>" +
"<th style='padding:8px 9px;text-align:left;color:$cMT;font-size:10px;font-weight:700;'>FAN</th>" +
"<th style='padding:8px 9px;text-align:left;color:$cMT;font-size:10px;font-weight:700;'>UPTIME</th>" +
"<th style='padding:8px 9px;text-align:left;color:$cMT;font-size:10px;font-weight:700;'>HW ERR</th>" +
"</tr></thead><tbody style='background:$cBG;'>$allRows</tbody></table>" +
"<div style='margin-top:20px;padding-top:14px;border-top:1px solid $cBR;color:$cMT;font-size:11px;text-align:center;'>RigAlert by ING Mining | $now</div>" +
"</td></tr></table></td></tr></table></body></html>"

# ── Send via Send-MailMessage ──────────────────────────────────────────────────
Write-Host ""
Write-Host "Sending to $($ToList.Count) recipient(s)..." -ForegroundColor Cyan
foreach ($addr in $ToList) { Write-Host "  -> $addr" }

try {
    Send-MailMessage `
        -From       $GmailUser `
        -To         $ToList `
        -Subject    $subj `
        -Body       $html `
        -BodyAsHtml `
        -SmtpServer "smtp.gmail.com" `
        -Port       587 `
        -UseSsl `
        -Credential $Cred `
        -ErrorAction Stop

    Write-Host ""
    Write-Host "Email sent!" -ForegroundColor Green
    Write-Host "Subject: $subj"
} catch {
    Write-Host ""
    Write-Host "FAILED: $_" -ForegroundColor Red
}
Write-Host ""
