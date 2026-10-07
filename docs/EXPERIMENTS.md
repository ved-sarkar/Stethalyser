# Experiment map

All supplied senders use 115200 baud. Matching baud rates alone does not make the sample formats compatible.

| Source | Intended rate | Wire format |
| --- | --- | --- |
| `arduino_mic.ino` | 8000 samples/s | One unsigned 8-bit byte per sample |
| `sketch_steth_streaming/sketch_steth_streaming.ino` | 44100 samples/s | One unsigned 8-bit byte per sample |
| `sketch_sep6a/sketch_sep6a.ino` | About 100 loop iterations/s | Decimal ASCII lines |
| `stethoscope_monitor.py` | 800 samples/s | Two bytes interpreted as signed little-endian 16-bit |
| `no filter.py` | 44100 samples/s | Two bytes interpreted as signed little-endian 16-bit |
| `MacBook Audio Playback Script.py` | 8000 samples/s | Two bytes interpreted as signed little-endian 16-bit |

No matching sender for the filtered 800 Hz receiver was found. Reading pairs of 8-bit samples as one 16-bit sample does not convert between these protocols. The 44100 Hz sender also requests more payload than a conventional 115200-baud UART can carry; no actual sample rate was measured.

The filtered monitor requests a 60–1000 Hz band but clamps the upper cutoff below the 400 Hz Nyquist limit of its configured 800 Hz stream. Filter state is reset per chunk. These choices need signal-level validation before drawing conclusions from the plot or recording.

The snapshot keeps the source variants separately and replaces only machine-specific serial device strings with `/dev/tty.YOUR_DEVICE`. No algorithm or protocol repair was made. The original empty Raspberry Pi attempt and an incomplete `playback.py` with an empty main block are omitted; the separate serial playback experiment is retained.

No hardware, audio device, recording, or dependency installation was used for packaging. Local output files are ignored. Use synthetic signals for future protocol and filter checks before handling any sensitive audio.
