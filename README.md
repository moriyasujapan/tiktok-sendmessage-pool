# TikTok SendMessage Microservice (Connection Pool)

# This product is currently under development

It provides a dedicated sendMessage API using @zerodytrash/TikTok-Live-Connector.

At startup, **log in to TikTok using Selenium → automatically obtain `sessionid` and `tt-target-idc`**,
and send data at high speed **by constantly reusing (pooling) the connection**.

> Note: This is an unofficial library. Its behavior may change with changes in TikTok specifications.

## Functions
- `POST /connect` ... Connect to the specified `uniqueId` (create a persistent connection)
- `POST /send` ... Send immediately using a persistent connection
- `POST /disconnect` ... Release the connection for the specified `uniqueId`
- `GET /health` ... Check health

## How to use (Docker)

```bash
cp .env.example .env # Edit as needed (manual login recommended the first time)
docker compose up
# → Complete the TikTok login in the Selenium browser to create cookies.json.
```

## How to send
### 1) Pre-connect (persistent connection)

```bash
curl -X POST http://localhost:3000/connect -H 'Content-Type: application/json' -d '{"uniqueId":"toba_aquarium"}'
```

### 2) Send message (immediately)
```bash
curl -X POST http://localhost:3000/send -H 'Content-Type: application/json' -d '{"uniqueId":"toba_aquarium","message":"Hello World"}'
```

###　3) Release the connection
```bash
curl -X POST http://localhost:3000/disconnect -H 'Content-Type: application/json' -d '{"uniqueId":"toba_aquarium"}'
```

## See ".env.example" for environment variables and files.

## cookies.json
The initial state is a placeholder "REPLACE". After Selenium starts, it will be replaced with the actual value.

```json
{
  "sessionid": "REPLACE",
  "tt-target-idc": "REPLACE"
}
```

