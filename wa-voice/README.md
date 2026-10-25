# wa-voice

A small Rust sidecar that places WhatsApp voice calls (via [whatsapp-rust](https://github.com/oxidezap/whatsapp-rust))
and streams the call audio over a localhost WebSocket. The Python bot (`squad/voice/bridge.py`) bridges that audio to
Gemini Live.

## Run

```sh
cd wa-voice
cargo run --release
```

State lives in `wa-voice/data/` (gitignored): `wa-voice.db` (the linked device) and, until paired, `wa-qr.txt`.

**Pairing (first start):** the QR string is logged and written to `data/wa-qr.txt`. Render it and scan it from
WhatsApp > Linked devices:

```sh
qrencode -t ansiutf8 < data/wa-qr.txt
```

The file is deleted once paired. `RUST_LOG=debug` shows call events.

## HTTP contract (`127.0.0.1:8091`)

| Request | Response |
| --- | --- |
| `GET /status` | `{"paired": bool, "connected": bool, "busy": bool}` |
| `POST /call` `{"phone": "+14805550123"}` | `200 {"call_id": "…"}` · `400` phone is not `+` and 10–15 digits · `409` a call is active · `503` not connected · `502` the call could not be placed |
| `GET /audio/<call_id>` | WebSocket (`404` for an unknown call) |

WebSocket frames:

- client → sidecar, binary: PCM16LE mono 16 kHz the callee hears, any length. It is re-chunked to 60 ms
  (960-sample) frames and played in real time; silence is sent when nothing is queued.
- sidecar → client, binary: PCM16LE mono 16 kHz from the callee.
- client → sidecar, text: `{"cmd":"hangup"}` ends the call. Closing the socket also ends it.
- sidecar → client, text: `{"event":"answered"}` once the callee picks up, `{"event":"ended","reason":"…"}` when the
  call is over.

One call at a time. A call is ended after 150 s regardless, so the sidecar never stays busy.

## Test

```sh
cargo test && cargo clippy -- -D warnings
```
