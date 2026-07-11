# Zoiper Configuration

Use account `1001` for AI calls. Account `1002` is optional and only needed for extension-to-extension SIP checks.

When the stack starts, copy the printed `Host / Domain` value from the `ZOIPER COPY-PASTE SETTINGS` block.

## Account 1001

- Username: `1001`
- Password: `1001pass`
- Domain: printed `Host / Domain`
- Port: `5060`
- Transport: UDP
- Call AI: `7000`

## Account 1002

- Username: `1002`
- Password: `1002pass`
- Domain: printed `Host / Domain`
- Port: `5060`
- Transport: UDP

Inbound AI test: call `7000` from `1001`.

Outbound AI test: trigger `POST /admin/start-outbound-zoiper/1001`, then answer the incoming Zoiper call.

On some Windows Docker Desktop setups, SIP/RTP over localhost can be sensitive. If registration fails, use the host LAN IP address instead of `127.0.0.1`.
