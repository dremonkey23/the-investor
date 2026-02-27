$h = @{
  "APCA-API-KEY-ID" = "PK5BLOFWV3NILHF75FSG4NQPKY"
  "APCA-API-SECRET-KEY" = "2NR9EKz7JEgPCHn2wP5rdM8NPn4VRBF8JdUMMsduX1Lg"
}
$base = "https://paper-api.alpaca.markets/v2"

# SELL: Trim DELL - sell 13 of 26 shares (lock in profits)
$body = @{symbol="DELL";qty="13";side="sell";type="market";time_in_force="day"} | ConvertTo-Json
Write-Host "=== SELL DELL 13 ==="
try { Invoke-RestMethod -Uri "$base/orders" -Method POST -Headers $h -Body $body -ContentType "application/json" | ConvertTo-Json } catch { Write-Host "ERROR: $_" }

# SELL: PLUG - 1 share (dead weight)
$body = @{symbol="PLUG";qty="1";side="sell";type="market";time_in_force="day"} | ConvertTo-Json
Write-Host "=== SELL PLUG 1 ==="
try { Invoke-RestMethod -Uri "$base/orders" -Method POST -Headers $h -Body $body -ContentType "application/json" | ConvertTo-Json } catch { Write-Host "ERROR: $_" }

# SELL: NIO - 2 shares (dead weight)
$body = @{symbol="NIO";qty="2";side="sell";type="market";time_in_force="day"} | ConvertTo-Json
Write-Host "=== SELL NIO 2 ==="
try { Invoke-RestMethod -Uri "$base/orders" -Method POST -Headers $h -Body $body -ContentType "application/json" | ConvertTo-Json } catch { Write-Host "ERROR: $_" }

# SELL: FSLY - all 217 shares (underperformer, -5.6%)
$body = @{symbol="FSLY";qty="217";side="sell";type="market";time_in_force="day"} | ConvertTo-Json
Write-Host "=== SELL FSLY 217 ==="
try { Invoke-RestMethod -Uri "$base/orders" -Method POST -Headers $h -Body $body -ContentType "application/json" | ConvertTo-Json } catch { Write-Host "ERROR: $_" }

Start-Sleep -Seconds 2

# BUY: LOGC - $12.3M insider buy signal, ~$2500 worth at ~$7 = 350 shares
$body = @{symbol="LOGC";qty="350";side="buy";type="market";time_in_force="day"} | ConvertTo-Json
Write-Host "=== BUY LOGC 350 ==="
try { Invoke-RestMethod -Uri "$base/orders" -Method POST -Headers $h -Body $body -ContentType "application/json" | ConvertTo-Json } catch { Write-Host "ERROR: $_" }

# BUY: MWA - CEO insider buy $739K, ~$2500 worth at ~$30 = 80 shares
$body = @{symbol="MWA";qty="80";side="buy";type="market";time_in_force="day"} | ConvertTo-Json
Write-Host "=== BUY MWA 80 ==="
try { Invoke-RestMethod -Uri "$base/orders" -Method POST -Headers $h -Body $body -ContentType "application/json" | ConvertTo-Json } catch { Write-Host "ERROR: $_" }

# BUY: AAT - insider buy $213K, ~$1000 worth at ~$20 = 50 shares  
$body = @{symbol="AAT";qty="50";side="buy";type="market";time_in_force="day"} | ConvertTo-Json
Write-Host "=== BUY AAT 50 ==="
try { Invoke-RestMethod -Uri "$base/orders" -Method POST -Headers $h -Body $body -ContentType "application/json" | ConvertTo-Json } catch { Write-Host "ERROR: $_" }
