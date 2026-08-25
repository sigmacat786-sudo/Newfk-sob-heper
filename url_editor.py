"""
url_editor.py
─────────────────────────────────────────────────────────────────────────────
Handles all the URL "editing" rules for Sobi Link Helper Bot.

There are 8 known URL shapes the bot can receive. Every shape ultimately gets
converted into a manifest URL (.../master.m3u8) and then wrapped into the
final onrender.com playable link.

Type 1 (FIXED)    -> .../master.mpd?...            => .../master.m3u8?...
Type 2 (FLEXIBLE) -> .../dash/<segments>/X.mp4?...  => .../master.m3u8?...
Type 3 (FIXED)    -> same as Type 1 (cloudfront/testwave hosts, longer URL)
Type 4 (FLEXIBLE) -> same as Type 2 (cloudfront/testwave hosts, longer URL)
Type 5 (FIXED)    -> strip "https://proxy.pwthor.live/play/" -> "https://"
                      then same as Type 1 (.../master.mpd? -> .../master.m3u8?)
Type 6 (FLEXIBLE) -> strip "https://proxy.pwthor.live/play/" -> "https://"
                      then same as Type 2 (.../dash/<segments>/X.mp4? -> .../master.m3u8?)
Type 7 (FIXED)    -> replace host "https://cloudfront.testwave.cc/"
                      -> "https://d1d34p8vz63oiq.cloudfront.net/"
                      then same as Type 1 (.../master.mpd? -> .../master.m3u8?)
Type 8 (FLEXIBLE) -> replace host "https://cloudfront.testwave.cc/"
                      -> "https://d1d34p8vz63oiq.cloudfront.net/"
                      then same as Type 2 (.../dash/<segments>/X.mp4? -> .../master.m3u8?)

The "FLEXIBLE" (dash) shape can appear with different path segments between
"/dash/" and the final "<file>.mp4?", depending on the quality/track the
source picked, e.g.:

    /dash/audio/2.mp4?
    /dash/720/2.mp4?
    /dash/1080/2.mp4?
    /dash/720/audio/2.mp4?
    /dash/<anything>/audio/<anything>.mp4?
    /dash/<anything>/<anything>.mp4?

All of these must be normalized the same way -> .../master.m3u8?
"""

import re
from urllib.parse import quote

from config import RENDER_PLAYER_BASE

# Proxy prefix that sometimes wraps a cloudfront URL. Always replaced with "https://"
PWTHOR_PROXY_PREFIX = re.compile(r"^https://proxy\.pwthor\.live/play/", re.IGNORECASE)

PWTHOR_LONG_PROXY_PREFIX = re.compile(r"https://p01--streamthorr--8zqnnv98yzb8.code.run/stream/", re.IGNORECASE)

# Pwthor cdn wala proxy prefix that sometimes wraps a cloudfront URL. Always replaced with "https://"
PWTHORcdn_PROXY_PREFIX = re.compile(r"^https://pwthorcdn.b-cdn.net/", re.IGNORECASE)

# Pwthor streamthor proxy prefix that sometimes wraps a cloudfront URL. Always replaced with "https://"
PWTHORstthor_PROXY_PREFIX = re.compile(r"^https://p01--streamthorr--8zqnnv98yzb8.code.run/", re.IGNORECASE)

# testwave host that always maps to the same fixed cloudfront host.
# Always replaced with "https://d1d34p8vz63oiq.cloudfront.net/"
TESTWAVE_HOST_PREFIX = re.compile(r"^https://cloudfront\.testwave\.cc/", re.IGNORECASE)

# subodhpgcollage host that always maps to the same fixed cloudfront host.
#compile(r^ itna rahne dena hai starting me and har word ke baad "\"lagana hai jaise
# aese https://stream.subodhpgcollege isko aese likhenge... https://stream\.subodhpgcollege\ okah!
# Always replaced with "https://d1d34p8vz63oiq.cloudfront.net/"
SUBODH_HOST_PREFIX = re.compile(r"^https://stream\.subodhpgcollege\.site/play/", re.IGNORECASE)

#and also pwthor+subodhpgcollage together wala
PWTHOR_SUBODH_HOST_PREFIX = re.compile(r"^https://pwthorproxy\.subodhpgcollege\.site/", re.IGNORECASE)

PWTHOR_LONNG_PROXY_PREFIX = re.compile(r"https://p01--streamthorr--fttnk8y47n9c.code.run/stream/", re.IGNORECASE)

####yaha se Alag startrs #####
#####
###okay yaha se
### done hu

# .../master.mpd?  ->  .../master.m3u8?
# NOTE: the "?" is now OPTIONAL — some links come with no query string at all
# (e.g. .../master.mpd with nothing after it), and those were being rejected
# before because the "?" was required.
MPD_PATTERN = re.compile(r"/master\.mpd\??", re.IGNORECASE)

# .../dash/<one or more path segments>/<file>.mp4?  ->  .../master.m3u8?
# Covers: /dash/audio/2.mp4?  /dash/720/2.mp4?  /dash/720/audio/2.mp4?
#         /dash/xxx/2.mp4?    /dash/xxx/audio/x.mp4?   etc.
# Also tolerates a "/mp4?" (slash instead of dot before mp4) variant.
# NOTE: the trailing "?" is now OPTIONAL here too, same reason as above.
DASH_AUDIO_PATTERN = re.compile(r"/dash/(?:[^/?]+/)+[^/?]+[./]mp4\??", re.IGNORECASE)


def _manifest_replacement(match: re.Match) -> str:
    """
    Build the replacement for a matched /master.mpd? or /dash/.../x.mp4?
    Keeps the trailing "?" only if the original match actually had one,
    so URLs with no query string don't get a stray "?" appended.
    """
    had_query_mark = match.group(0).endswith("?")
    return "/master.m3u8?" if had_query_mark else "/master.m3u8"


def edit_video_url(raw_url: str) -> str | None:
    """
    Apply the correct edit rule to a raw video URL based on its shape.
    Returns the edited (manifest) URL, or None if the URL doesn't match
    any known pattern.
    """
    url = raw_url.strip()

    # Step 1: strip pwthor proxy prefix if present (Type 5 & 6)
    if PWTHOR_PROXY_PREFIX.match(url):
        url = PWTHOR_PROXY_PREFIX.sub("https://", url)

   # Step 111: strip pwthor long proxy prefix if present (Type 5 & 6)
    if PWTHOR_LONG_PROXY_PREFIX.match(url):
        url = PWTHOR_LONG_PROXY_PREFIX.sub("https://p01--streamthorr--8zqnnv98yzb8.code.run/stream/", url)

    if PWTHOR_LONNG_PROXY_PREFIX.match(url):
        url = PWTHOR_LONNG_PROXY_PREFIX.sub("https://p01--streamthorr--fttnk8y47n9c.code.run/stream/", url) #Double NN hai LONNG yahi diffrence hai bro.

    # Step extra: strip Subhodpgcollage prefix if present (Type new)
    if SUBODH_HOST_PREFIX.match(url):
        url = SUBODH_HOST_PREFIX.sub("https://", url)

  # Step together extra: strip PWthor and Subhodpgcollage prefix if present (Type new)
    if PWTHOR_SUBODH_HOST_PREFIX.match(url):
        url = PWTHOR_SUBODH_HOST_PREFIX.sub("https://d1d34p8vz63oiq.cloudfront.net/", url)

    # Step 1b: replace testwave host with the fixed cloudfront host (Type 7 & 8)
    if TESTWAVE_HOST_PREFIX.match(url):
        url = TESTWAVE_HOST_PREFIX.sub("https://d1d34p8vz63oiq.cloudfront.net/", url)

    # Step pwthor cdn wala: strip pwthor proxy prefix if present (Type 5 & 6)
    if PWTHORcdn_PROXY_PREFIX.match(url):
        url = PWTHORcdn_PROXY_PREFIX.sub("https://d1d34p8vz63oiq.cloudfront.net/", url)

   # Step pwthor streamthor(stthor): strip pwthor proxy prefix if present (Type 5 & 6)
    if PWTHORstthor_PROXY_PREFIX.match(url):
        url = PWTHORstthor_PROXY_PREFIX.sub("https://p01--streamthorr--8zqnnv98yzb8.code.run/", url)

    # Step 2: apply the manifest replacement
    if MPD_PATTERN.search(url):
        return MPD_PATTERN.sub(_manifest_replacement, url)

    if DASH_AUDIO_PATTERN.search(url):
        return DASH_AUDIO_PATTERN.sub(_manifest_replacement, url)

    return None


def build_render_url(edited_url: str) -> str:
    """
    Wrap an edited (manifest) URL into the final onrender.com playable link.
    """
    encoded = quote(edited_url, safe="")
    return f"{RENDER_PLAYER_BASE}{encoded}"


def process_raw_url(raw_url: str) -> str | None:
    """
    Full pipeline: raw user URL -> edited manifest URL -> final onrender.com URL.
    Returns None if the URL isn't recognized.
    """
    edited = edit_video_url(raw_url)
    if edited is None:
        return None
    return build_render_url(edited)


def looks_like_url(text: str) -> bool:
    """Quick check: does this message start like a URL?"""
    t = text.strip()
    return t.startswith("http://") or t.startswith("https://")
