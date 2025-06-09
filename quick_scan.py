# quick_scan.py
import os
import regex as re

# Precompile combined full + partial CC patterns
FAST_CC_RE = re.compile(
    br"\b(?:"
    br"4[0-9]{3}(?:[ -]?[0-9]{4}){3}|"
    br"5[1-5][0-9]{2}(?:[ -]?[0-9]{4}){3}|"
    br"3[47][0-9]{2}(?:[ -]?[0-9]{4}){2}|"
    br"6(?:011|5[0-9]{2})(?:[ -]?[0-9]{4}){3}|"
    br"(?:\d[ -]?){12}"
    br")\b"
)

def quick_cc_scan(path, head=65536, tail=65536):
    """
    Read up to head bytes from start and tail bytes from end,
    apply FAST_CC_RE, return True if any match.
    """
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as f:
            data = f.read(head)
            if size > head:
                f.seek(max(size - tail, head))
                data += f.read(tail)
        return bool(FAST_CC_RE.search(data))
    except Exception:
        return False
