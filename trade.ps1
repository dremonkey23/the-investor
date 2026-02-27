$h = @{
  'APCA-API-KEY-ID'='PK5BLOFWV3NILHF75FSG4NQPKY'
  'APCA-API-SECRET-KEY'='2NR9EKz7JEgPCHn2wP5rdM8NPn4VRBF8JdUMMsduX1Lg'
}

# Get latest quotes for sizing
$symbols = @('NVDA','MSFT','GS','COHR','FSLY','CGAU')
foreach ($sym in $symbols) {
  $q = Invoke-RestMethod -Uri "https://data.alpaca.markets/v2/stocks/$sym/quotes/latest" -Headers $h
  Write-Output "$sym ask: $($q.quote.ap)"
}

# Place orders - Safe Plays
$orders = @(
  @{symbol='NVDA'; notional='8000'; side='buy'; type='market'; time_in_force='day'},
  @{symbol='MSFT'; notional='8000'; side='buy'; type='market'; time_in_force='day'},
  @{symbol='GS';   notional='7000'; side='buy'; type='market'; time_in_force='day'},
  # Risky Plays
  @{symbol='COHR'; notional='5000'; side='buy'; type='market'; time_in_force='day'},
  @{symbol='FSLY'; notional='4000'; side='buy'; type='market'; time_in_force='day'},
  @{symbol='CGAU'; notional='4000'; side='buy'; type='market'; time_in_force='day'}
)

foreach ($o in $orders) {
  $body = $o | ConvertTo-Json
  Write-Output "Placing order: $($o.symbol) - $($o.notional)"
  try {
    $result = Invoke-RestMethod -Uri 'https://paper-api.alpaca.markets/v2/orders' -Method Post -Headers $h -ContentType 'application/json' -Body $body
    Write-Output "  OK: id=$($result.id) status=$($result.status)"
  } catch {
    Write-Output "  ERROR: $_"
  }
}
