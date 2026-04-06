# Execution Flow

1. Client sends execution request to Relay Server.
2. Relay Server validates request using Policy Engine.
3. If approved, Relay issues execution token.
4. Relay forwards request to Endpoint.
5. Endpoint verifies token.
6. If valid, Endpoint executes operation.
7. Execution result returned to Relay.
8. Audit log recorded.
