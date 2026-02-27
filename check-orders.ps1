$h = @{
  "APCA-API-KEY-ID" = "PK5BLOFWV3NILHF75FSG4NQPKY"
  "APCA-API-SECRET-KEY" = "2NR9EKz7JEgPCHn2wP5rdM8NPn4VRBF8JdUMMsduX1Lg"
}
$base = "https://paper-api.alpaca.markets/v2"

$ids = @(
  "e2773545-517b-49a2-9136-06c5c84be174",  # DELL sell
  "bc952cd0-8b73-4a8a-803a-b977e386ebb2",  # PLUG sell
  "3974f856-227a-4533-ac65-7768d6cfbfb5",  # NIO sell
  "9042243f-753d-4633-a5cd-85f2e30cd27f",  # FSLY sell
  "d6245538-2ed9-4269-b6f0-866f3fb80961",  # MWA buy
  "3c21f793-89e4-4640-a2d6-f871d432d570"   # AAT buy
)

foreach ($id in $ids) {
  $order = Invoke-RestMethod -Uri "$base/orders/$id" -Headers $h
  Write-Host "$($order.symbol) $($order.side) $($order.qty) | status=$($order.status) | filled_qty=$($order.filled_qty) | filled_avg_price=$($order.filled_avg_price)"
}
