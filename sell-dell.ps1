$headers = @{
    "APCA-API-KEY-ID" = "PK5BLOFWV3NILHF75FSG4NQPKY"
    "APCA-API-SECRET-KEY" = "2NR9EKz7JEgPCHn2wP5rdM8NPn4VRBF8JdUMMsduX1Lg"
}
$body = @{
    symbol = "DELL"
    qty = "3"
    side = "sell"
    type = "market"
    time_in_force = "day"
} | ConvertTo-Json

$result = Invoke-RestMethod -Method POST -Uri "https://paper-api.alpaca.markets/v2/orders" -Headers $headers -ContentType "application/json" -Body $body
$result | ConvertTo-Json
