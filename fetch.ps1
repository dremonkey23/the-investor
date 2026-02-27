$h = @{
  'APCA-API-KEY-ID'='PK5BLOFWV3NILHF75FSG4NQPKY'
  'APCA-API-SECRET-KEY'='2NR9EKz7JEgPCHn2wP5rdM8NPn4VRBF8JdUMMsduX1Lg'
}
Write-Output "=== ACCOUNT ==="
Invoke-RestMethod -Uri 'https://paper-api.alpaca.markets/v2/account' -Headers $h | ConvertTo-Json
Write-Output "=== POSITIONS ==="
try {
  $pos = Invoke-RestMethod -Uri 'https://paper-api.alpaca.markets/v2/positions' -Headers $h
  $pos | ConvertTo-Json -Depth 5
} catch {
  Write-Output "No positions or error: $_"
}
Write-Output "=== OPEN ORDERS ==="
try {
  $ord = Invoke-RestMethod -Uri 'https://paper-api.alpaca.markets/v2/orders?status=open' -Headers $h
  $ord | ConvertTo-Json -Depth 5
} catch {
  Write-Output "No open orders or error: $_"
}
