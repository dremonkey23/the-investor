$headers = @{
    "APCA-API-KEY-ID" = "PK5BLOFWV3NILHF75FSG4NQPKY"
    "APCA-API-SECRET-KEY" = "2NR9EKz7JEgPCHn2wP5rdM8NPn4VRBF8JdUMMsduX1Lg"
}

# Check DELL sell fill
Write-Host "=== DELL SELL ORDER ==="
$dell = Invoke-RestMethod -Uri "https://paper-api.alpaca.markets/v2/orders/9ff7faf5-6cd0-4c00-b464-946662bee4d6" -Headers $headers
$dell | ConvertTo-Json

# Check account cash
Write-Host "`n=== ACCOUNT ==="
$acct = Invoke-RestMethod -Uri "https://paper-api.alpaca.markets/v2/account" -Headers $headers
Write-Host "Cash: $($acct.cash) | Buying Power: $($acct.buying_power)"
