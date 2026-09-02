# filepath: src/bot/presets.py
"""
Read-pacing presets — adjustable from the bot UI, not just `.env`.

PHILOSOPHY
==========
Most users should NEVER need to edit `.env` to change read speed. The bot
exposes three one-click presets that cover ~99% of use cases:

  * SAFE   — slowest, most human-like. 1 message/sec.
             Best for: occasional scans, peace of mind, large accounts.
  * NORMAL — default, balanced. ~10 messages/sec with periodic breaths.
             Best for: regular use; the recommended starting point.
  * FAST   — quicker, higher risk. ~40 messages/sec.
             Best for: small personal chats, dev/testing.

For custom values (e.g. power users wanting 2 msg/sec or 100 msg/sec), the
custom option lets you type the four values directly in the bot — NO `.env`
edit needed.

The values are pre-baked in code so we can present a friendly description
in the UI. The user's choice persists in `UserState.pace_preset`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

PacePreset = Literal["safe", "normal", "fast", "custom"]


@dataclass(slots=True, frozen=True)
class PaceConfig:
    """Concrete pacing values used by `fetch_messages`."""

    name_preset: str
    label_fa: str
    label_en: str
    desc_fa: str
    desc_en: str
    # Pacing parameters:
    slow_read_enabled: bool
    fast_batch_size: int
    fast_batch_delay: float
    batch_size: int
    long_pause_delay: float

    def rate_per_second(self) -> float:
        """Approximate throughput in messages/second (excluding long pauses)."""
        if not self.slow_read_enabled or self.fast_batch_delay <= 0:
            return float("inf")
        return self.fast_batch_size / self.fast_batch_delay


# ----------------------------------------------------------------------
# Presets
# ----------------------------------------------------------------------

PRESET_SAFE = PaceConfig(
    name_preset="safe",
    label_fa="🛡 امن (۱ پیام/ثانیه)",
    label_en="🛡 Safe (1 msg/sec)",
    desc_fa=(
        "کندترین حالت — حدود ۱ پیام در ثانیه. "
        "کمترین ریسک ban؛ بهترین برای اکانت‌های مهم یا چت‌های شلوغ."
    ),
    desc_en=(
        "Slowest mode — about 1 message per second. "
        "Lowest ban risk; best for important accounts or busy chats."
    ),
    slow_read_enabled=True,
    fast_batch_size=1,
    fast_batch_delay=1.0,
    batch_size=20,
    long_pause_delay=10.0,
)

PRESET_NORMAL = PaceConfig(
    name_preset="normal",
    label_fa="⚖ عادی (۱۰ پیام/ثانیه) — پیش‌فرض",
    label_en="⚖ Normal (10 msg/sec) — default",
    desc_fa=(
        "تعادل بین سرعت و امنیت — ۱۰ پیام/ثانیه با مکث ۵ ثانیه هر ۵۰ پیام. "
        "مناسب برای استفاده‌ی روزمره."
    ),
    desc_en=(
        "Balance of speed and safety — 10 msg/sec with a 5-second "
        "pause every 50 messages. Good for daily use."
    ),
    slow_read_enabled=True,
    fast_batch_size=10,
    fast_batch_delay=1.0,
    batch_size=50,
    long_pause_delay=5.0,
)

PRESET_FAST = PaceConfig(
    name_preset="fast",
    label_fa="🚀 سریع (۴۰ پیام/ثانیه)",
    label_en="🚀 Fast (40 msg/sec)",
    desc_fa=(
        "سریع‌تر — حدود ۴۰ پیام در ثانیه. "
        "⚠️ ریسک بیشتر ban؛ فقط برای چت‌های کوچک یا تست."
    ),
    desc_en=(
        "Faster — about 40 messages per second. "
        "⚠️ Higher ban risk; only for small chats or testing."
    ),
    slow_read_enabled=True,
    fast_batch_size=20,
    fast_batch_delay=0.5,
    batch_size=100,
    long_pause_delay=3.0,
)

PRESETS: dict[str, PaceConfig] = {
    "safe": PRESET_SAFE,
    "normal": PRESET_NORMAL,
    "fast": PRESET_FAST,
}


def get_preset(name: str) -> PaceConfig:
    """Return the preset by name, falling back to NORMAL."""
    return PRESETS.get(name, PRESET_NORMAL)


def all_presets() -> list[PaceConfig]:
    """Return all built-in presets (excludes 'custom')."""
    return [PRESET_SAFE, PRESET_NORMAL, PRESET_FAST]
