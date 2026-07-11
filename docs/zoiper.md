# Zoiper Configuration

Use two SIP accounts for local testing.

## Account 1001

- Username: `1001`
- Password: `1001pass`
- Domain: `127.0.0.1`
- Port: `5060`
- Transport: UDP

## Account 1002

- Username: `1002`
- Password: `1002pass`
- Domain: `127.0.0.1`
- Port: `5060`
- Transport: UDP

After both accounts register, call `1002` from `1001`, or call `1001` from `1002`.

On some Windows Docker Desktop setups, SIP/RTP over localhost can be sensitive. If registration fails, use the host LAN IP address instead of `127.0.0.1`.
