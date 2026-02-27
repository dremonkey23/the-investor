$h = @{
  'APCA-API-KEY-ID'='PK5BLOFWV3NILHF75FSG4NQPKY'
  'APCA-API-SECRET-KEY'='2NR9EKz7JEgPCHn2wP5rdM8NPn4VRBF8JdUMMsduX1Lg'
}
Write-Output "=== POSITIONS ==="
Invoke-RestMethod -Uri 'https://paper-api.alpaca.markets/v2/positions' -Headers $h | ForEach-Object {
  Write-Output "$($_.symbol): qty=$($_.qty) avg=$($_.avg_entry_price) mkt=$($_.current_price) P/L=$($_.unrealized_pl) ($($_.unrealized_plpc)%)"
}
Write-Output "=== ACCOUNT ==="
$a = Invoke-RestMethod -Uri 'https://paper-api.alpaca.markets/v2/account' -Headers $h
Write-Output "Cash: $($a.cash) | Equity: $($a.equity) | Portfolio: $($a.portfolio_value)"
