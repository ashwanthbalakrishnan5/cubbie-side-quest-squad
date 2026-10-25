//! PCM16LE byte stream <-> 960-sample i16 frames (16 kHz mono, 60 ms).

/// Drain every whole `frame`-sample frame from `buf`, keeping the remainder for the next call.
pub fn bytes_to_frames(buf: &mut Vec<u8>, frame: usize) -> Vec<Vec<i16>> {
    let whole = buf.len() / (frame * 2) * frame * 2;
    let frames = buf[..whole]
        .chunks_exact(frame * 2)
        .map(|f| {
            f.as_chunks::<2>()
                .0
                .iter()
                .map(|b| i16::from_le_bytes(*b))
                .collect()
        })
        .collect();
    buf.drain(..whole);
    frames
}

pub fn frame_to_bytes(frame: &[i16]) -> Vec<u8> {
    frame.iter().flat_map(|s| s.to_le_bytes()).collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn chunks_and_keeps_remainder() {
        let mut buf = vec![0u8; 2000];
        let frames = bytes_to_frames(&mut buf, 960);
        assert_eq!(frames.len(), 1);
        assert_eq!(frames[0].len(), 960);
        assert_eq!(buf.len(), 80);
    }

    #[test]
    fn roundtrip_little_endian() {
        let frame: Vec<i16> = vec![1, -2, 0x1234, i16::MIN, i16::MAX];
        let bytes = frame_to_bytes(&frame);
        assert_eq!(&bytes[..6], &[1, 0, 0xFE, 0xFF, 0x34, 0x12]);
        let mut buf = bytes;
        assert_eq!(bytes_to_frames(&mut buf, frame.len()), vec![frame]);
        assert!(buf.is_empty());
    }
}
