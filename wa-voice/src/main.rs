//! wa-voice: places WhatsApp voice calls and pipes 16 kHz PCM over a localhost WebSocket.
//! HTTP contract: see README.md.

mod audio;

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use std::time::Duration;

use anyhow::{Result, anyhow};
use axum::Json;
use axum::Router;
use axum::extract::ws::{Message, WebSocket, WebSocketUpgrade};
use axum::extract::{Path, State};
use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};
use axum::routing::{get, post};
use log::{info, warn};
use serde::Deserialize;
use serde_json::json;
use tokio::time::{interval, sleep, timeout};
use wacore::voip::CallEvent;
use whatsapp_rust::prelude::*;
use whatsapp_rust::voip::CallHandle;

use audio::{bytes_to_frames, frame_to_bytes};

const LISTEN: &str = "127.0.0.1:8091";
const DB_PATH: &str = "data/wa-voice.db";
const QR_FILE: &str = "data/wa-qr.txt";
/// 60 ms of 16 kHz mono, the frame size the call engine requires.
const FRAME: usize = 960;
const FRAME_TIME: Duration = Duration::from_millis(60);
/// Safety net so a call nobody hangs up never leaves the sidecar busy.
const MAX_CALL: Duration = Duration::from_secs(150);
/// WhatsApp never times out an unanswered offer for us; the bot waits at most 40 s.
const RING_TIMEOUT: Duration = Duration::from_secs(35);

struct Call {
    id: String,
    handle: Arc<CallHandle>,
    /// Frames the callee should hear; the pacer feeds them to the engine in real time.
    pcm_in: async_channel::Sender<Vec<i16>>,
    /// Decoded frames from the callee.
    speaker: async_channel::Receiver<Vec<i16>>,
    reason: Arc<Mutex<String>>,
}

impl Call {
    fn set_reason(&self, reason: &str) {
        set_reason(&self.reason, reason);
    }
    fn reason(&self) -> String {
        self.reason
            .lock()
            .unwrap_or_else(|e| e.into_inner())
            .clone()
    }
}

/// Keep the first specific reason; later ones (e.g. the media close after our hangup) don't override it.
fn set_reason(slot: &Mutex<String>, reason: &str) {
    let mut r = slot.lock().unwrap_or_else(|e| e.into_inner());
    if r.is_empty() {
        *r = reason.to_string();
    }
}

struct App {
    client: Arc<Client>,
    paired: Arc<AtomicBool>,
    /// tokio Mutex: held across `start()` so two POST /call can't both dial.
    call: tokio::sync::Mutex<Option<Arc<Call>>>,
}

/// `+` then 10-15 digits -> the digits.
fn valid_phone(phone: &str) -> Option<&str> {
    let digits = phone.strip_prefix('+')?;
    ((10..=15).contains(&digits.len()) && digits.bytes().all(|b| b.is_ascii_digit()))
        .then_some(digits)
}

fn error(code: StatusCode, msg: &str) -> Response {
    (code, Json(json!({ "error": msg }))).into_response()
}

async fn status(State(app): State<Arc<App>>) -> Json<serde_json::Value> {
    // A locked slot means a call is being placed right now.
    let busy = app.call.try_lock().map_or(true, |c| c.is_some());
    Json(json!({
        "paired": app.paired.load(Ordering::SeqCst),
        "connected": app.client.is_session_ready(),
        "busy": busy,
    }))
}

#[derive(Deserialize)]
struct CallRequest {
    phone: String,
}

/// Body parsed by hand so callers need no `Content-Type: application/json` (e.g. `curl -d`).
async fn place_call(State(app): State<Arc<App>>, body: axum::body::Bytes) -> Response {
    let req: CallRequest = match serde_json::from_slice(&body) {
        Ok(req) => req,
        Err(e) => return error(StatusCode::BAD_REQUEST, &format!("bad json: {e}")),
    };
    let Some(digits) = valid_phone(req.phone.trim()) else {
        return error(StatusCode::BAD_REQUEST, "phone must be + and 10-15 digits");
    };
    let mut slot = app.call.lock().await;
    if slot.is_some() {
        return error(StatusCode::CONFLICT, "a call is already active");
    }
    if !app.client.is_session_ready() {
        return error(StatusCode::SERVICE_UNAVAILABLE, "whatsapp is not connected");
    }
    let jid: Jid = match format!("{digits}@s.whatsapp.net").parse() {
        Ok(jid) => jid,
        Err(e) => return error(StatusCode::BAD_REQUEST, &format!("bad jid: {e}")),
    };

    let (pcm_in, queue) = async_channel::unbounded::<Vec<i16>>();
    let (mic_tx, mic_rx) = async_channel::bounded::<Vec<i16>>(8);
    let (speaker_tx, speaker_rx) = async_channel::bounded::<Vec<i16>>(64);
    info!("placing call to {jid}");
    let handle = match app
        .client
        .voip()
        .call(&jid)
        .audio(mic_rx, speaker_tx)
        .start()
        .await
    {
        Ok(handle) => Arc::new(handle),
        Err(e) => {
            warn!("call failed: {e}");
            return error(StatusCode::BAD_GATEWAY, &format!("call failed: {e}"));
        }
    };
    let call = Arc::new(Call {
        id: handle.call_id().to_string(),
        handle: handle.clone(),
        pcm_in,
        speaker: speaker_rx,
        reason: Arc::new(Mutex::new(String::new())),
    });
    info!("call {} offered", call.id);

    // Record why media closed, for the `ended` event.
    if let Some(mut events) = handle.take_events() {
        let reason = call.reason.clone();
        tokio::spawn(async move {
            while let Ok(ev) = events.recv().await {
                match ev {
                    CallEvent::Closed(r) => set_reason(&reason, &format!("{r:?}")),
                    other => log::debug!("call event: {other:?}"),
                }
            }
        });
    }

    // Pacer: one frame every 60 ms, silence when the bridge has nothing queued.
    let h = handle.clone();
    tokio::spawn(async move {
        let mut tick = interval(FRAME_TIME);
        loop {
            tokio::select! {
                _ = h.wait_ended() => break,
                _ = tick.tick() => {
                    let frame = queue.try_recv().unwrap_or_else(|_| vec![0; FRAME]);
                    let _ = mic_tx.try_send(frame);
                }
            }
        }
    });

    // Watcher: end unanswered or overlong calls, free the slot when the call ends.
    let (app2, c) = (app.clone(), call.clone());
    tokio::spawn(async move {
        let picked_up = async {
            while !c.handle.media_connected() {
                sleep(Duration::from_millis(200)).await;
            }
        };
        match ring(c.handle.wait_ended(), picked_up).await {
            // A <reject> ends the call before media connects.
            Ring::Ended => c.set_reason("declined"),
            Ring::NoAnswer => {
                c.set_reason("no answer");
                c.handle.terminate().await;
            }
            Ring::Answered => {
                if timeout(MAX_CALL, c.handle.wait_ended()).await.is_err() {
                    c.set_reason("max duration");
                    c.handle.terminate().await;
                }
            }
        }
        info!("call {} ended: {}", c.id, c.reason());
        let mut slot = app2.call.lock().await;
        if slot.as_ref().is_some_and(|s| s.id == c.id) {
            *slot = None;
        }
    });

    *slot = Some(call.clone());
    Json(json!({ "call_id": call.id })).into_response()
}

#[derive(Debug, PartialEq)]
enum Ring {
    Answered,
    Ended,
    NoAnswer,
}

/// The ringing phase: whichever of hang-up, pick-up or `RING_TIMEOUT` comes first.
async fn ring(ended: impl Future<Output = ()>, picked_up: impl Future<Output = ()>) -> Ring {
    tokio::select! {
        biased;
        _ = ended => Ring::Ended,
        _ = picked_up => Ring::Answered,
        _ = sleep(RING_TIMEOUT) => Ring::NoAnswer,
    }
}

async fn audio_ws(
    ws: WebSocketUpgrade,
    Path(call_id): Path<String>,
    State(app): State<Arc<App>>,
) -> Response {
    let call = app.call.lock().await.clone().filter(|c| c.id == call_id);
    match call {
        Some(call) => ws.on_upgrade(move |socket| pump(socket, call)),
        None => error(StatusCode::NOT_FOUND, "no such call"),
    }
}

fn is_hangup(text: &str) -> bool {
    serde_json::from_str::<serde_json::Value>(text).is_ok_and(|v| v["cmd"] == "hangup")
}

async fn pump(mut ws: WebSocket, call: Arc<Call>) {
    let mut buf = Vec::new();
    let mut answered = false;
    let mut poll = interval(Duration::from_millis(200));
    loop {
        tokio::select! {
            msg = ws.recv() => match msg {
                Some(Ok(Message::Binary(bytes))) => {
                    buf.extend_from_slice(&bytes);
                    for frame in bytes_to_frames(&mut buf, FRAME) {
                        let _ = call.pcm_in.try_send(frame);
                    }
                }
                Some(Ok(Message::Text(text))) if is_hangup(&text) => {
                    call.set_reason("hangup");
                    call.handle.terminate().await;
                }
                Some(Ok(_)) => {}
                // Bridge went away: don't leave the callee on an open line.
                _ => {
                    call.set_reason("bridge disconnected");
                    call.handle.terminate().await;
                    break;
                }
            },
            Ok(frame) = call.speaker.recv() => {
                if ws.send(Message::Binary(frame_to_bytes(&frame).into())).await.is_err() {
                    call.set_reason("bridge disconnected");
                    call.handle.terminate().await;
                    break;
                }
            }
            _ = call.handle.wait_ended() => {
                let reason = match call.reason() {
                    r if r.is_empty() => "ended".to_string(),
                    r => r,
                };
                let event = json!({ "event": "ended", "reason": reason }).to_string();
                let _ = ws.send(Message::Text(event.into())).await;
                break;
            }
            _ = poll.tick(), if !answered => {
                // Outgoing call: true once the callee accepted and media keys are installed.
                if call.handle.media_connected() {
                    answered = true;
                    let event = json!({ "event": "answered" }).to_string();
                    let _ = ws.send(Message::Text(event.into())).await;
                }
            }
        }
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    env_logger::Builder::from_env(
        env_logger::Env::default().default_filter_or("info,webrtc_sctp=error,webrtc_dtls=error"),
    )
    .init();
    std::fs::create_dir_all("data")?;
    let store = SqliteStore::open(DB_PATH)
        .await
        .map_err(|e| anyhow!("sqlite: {e}"))?;
    let paired = Arc::new(AtomicBool::new(false));
    let flag = paired.clone();
    let bot = Bot::builder()
        .with_backend(store)
        .on_qr_code(|code, valid| async move {
            info!(
                "Scan this QR (valid {}s), also in {QR_FILE}:\n{code}",
                valid.as_secs()
            );
            if let Err(e) = std::fs::write(QR_FILE, &code) {
                warn!("could not write {QR_FILE}: {e}");
            }
        })
        .on_event_for(
            &[
                EventKind::Connected,
                EventKind::PairSuccess,
                EventKind::LoggedOut,
            ],
            move |event, _client| {
                let flag = flag.clone();
                async move {
                    let ok = !matches!(&*event, Event::LoggedOut(_));
                    flag.store(ok, Ordering::SeqCst);
                    if ok {
                        let _ = std::fs::remove_file(QR_FILE);
                        info!("whatsapp paired and connected");
                    } else {
                        warn!("whatsapp logged out; restart to pair again");
                    }
                }
            },
        )
        .build()
        .await
        .map_err(|e| anyhow!("build bot: {e}"))?;

    let app = Arc::new(App {
        client: bot.client(),
        paired,
        call: tokio::sync::Mutex::new(None),
    });
    let router = Router::new()
        .route("/status", get(status))
        .route("/call", post(place_call))
        .route("/audio/{call_id}", get(audio_ws))
        .with_state(app);
    let listener = tokio::net::TcpListener::bind(LISTEN).await?;
    info!("wa-voice listening on http://{LISTEN}");

    tokio::select! {
        reason = bot.run() => warn!("whatsapp client stopped: {reason:?}"),
        served = axum::serve(listener, router) => served?,
        _ = shutdown_signal() => info!("shutting down"),
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn phone_validation() {
        assert_eq!(valid_phone("+14805550123"), Some("14805550123"));
        assert_eq!(valid_phone("+123456789012345"), Some("123456789012345"));
        assert_eq!(valid_phone("14805550123"), None);
        assert_eq!(valid_phone("+123456789"), None);
        assert_eq!(valid_phone("+1234567890123456"), None);
        assert_eq!(valid_phone("+1 480 555 0123"), None);
    }

    #[tokio::test(start_paused = true)]
    async fn ring_outcomes() {
        use std::future::{pending, ready};
        let t0 = tokio::time::Instant::now();
        assert_eq!(ring(pending(), pending()).await, Ring::NoAnswer);
        assert_eq!(t0.elapsed(), RING_TIMEOUT);
        assert_eq!(ring(ready(()), pending()).await, Ring::Ended);
        assert_eq!(
            ring(pending(), sleep(Duration::from_secs(5))).await,
            Ring::Answered
        );
    }

    #[test]
    fn hangup_command() {
        assert!(is_hangup(r#"{"cmd":"hangup"}"#));
        assert!(!is_hangup(r#"{"cmd":"other"}"#));
        assert!(!is_hangup("hangup"));
    }
}
