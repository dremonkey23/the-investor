$headers = @{
    "APCA-API-KEY-ID" = "PK5BLOFWV3NILHF75FSG4NQPKY"
    "APCA-API-SECRET-KEY" = "2NR9EKz7JEgPCHn2wP5rdM8NPn4VRBF8JdUMMsduX1Lg"
}

# Buy LOGC - $12.3M insider purchase signal (~$400 deployment, keeping some cash reserve)
$body = @{
    symbol = "LOGC"
    qty = "55"
    side = "buy"
    type = "market"
    time_in_force = "day"
} | ConvertTo-Json

$result = Invoke-RestMethod -Method POST -Uri "https://paper-api.alpaca.markets/v2/orders" -Headers $headers -ContentType "application/json" -Body $body
$result | ConvertTo-Json
