"""24 kHz -> 16 kHz PCM16LE mono resampling with the stdlib only."""

import sys
from array import array

_GROUP = 6  # 3 input samples * 2 bytes -> 2 output samples


def pcm16_24k_to_16k(data: bytes, carry: bytes = b"") -> tuple[bytes, bytes]:
    """Resample by linear interpolation (3 samples -> 2); returns (output, leftover)."""
    buf = carry + data
    n = len(buf) // _GROUP * _GROUP
    src = array("h", buf[:n])
    if sys.byteorder == "big":
        src.byteswap()
    out = array("h", bytes(n // 3 * 2))
    out[0::2] = src[0::3]  # output 2k sits on input 3k
    # output 2k+1 sits at input 3k+1.5, halfway between 3k+1 and 3k+2
    out[1::2] = array("h", ((a + b) // 2 for a, b in zip(src[1::3], src[2::3])))
    if sys.byteorder == "big":
        out.byteswap()
    return out.tobytes(), buf[n:]
