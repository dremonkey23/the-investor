$h = @{
  "APCA-API-KEY-ID" = "PK5BLOFWV3NILHF75FSG4NQPKY"
  "APCA-API-SECRET-KEY" = "2NR9EKz7JEgPCHn2wP5rdM8NPn4VRBF8JdUMMsduX1Lg"
}

Write-Host "=== ACCOUNT ==="
$acct = Invoke-RestMethod -Uri "https://paper-api.alpaca.markets/v2/account" -Headers $h
$acct | ConvertTo-Json

Write-Host "=== POSITIONS ==="
try {
  $pos = Invoke-RestMethod -Uri "https://paper-api.alpaca.markets/v2/positions" -Headers $h
  $pos | ConvertTo-Json -Depth 5
} catch {
  Write-Host "No positions or error: $_"
}

Write-Host "=== OPEN ORDERS ==="
try {
  $orders = Invoke-RestMethod -Uri "https://paper-api.alpaca.markets/v2/orders?status=open" -Headers $h
  $orders | ConvertTo-Json -Depth 5
} catch {
  Write-Host "No open orders or error: $_"
}
