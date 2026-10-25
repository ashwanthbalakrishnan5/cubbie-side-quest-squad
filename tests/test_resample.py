import math
from array import array

from squad.voice.resample import pcm16_24k_to_16k


def _tone(n: int) -> bytes:
    return array("h", (int(8000 * math.sin(i / 7)) for i in range(n))).tobytes()


def test_resample_length_ratio():
    out, carry = pcm16_24k_to_16k(_tone(2400))
    assert len(out) == 1600 * 2
    assert carry == b""


def test_resample_carry_between_chunks():
    data = _tone(2401) + b"\x01"  # odd sample count plus a stray byte
    whole, whole_carry = pcm16_24k_to_16k(data)
    out, carry = b"", b""
    for i in range(0, len(data), 997):  # odd chunk size splits samples mid-byte
        chunk, carry = pcm16_24k_to_16k(data[i : i + 997], carry)
        out += chunk
    assert out == whole
    assert carry == whole_carry
