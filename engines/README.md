# Engine Installation Instructions

To use the multi-engine support for chess variants, you need to download and install the appropriate engines.

## Fairy-Stockfish (for Chess960, Atomic, and Horde)

1. Download Fairy-Stockfish from: https://github.com/ianfab/Fairy-Stockfish/releases
2. Extract the appropriate binary for your system (Windows/Linux/macOS)
3. Rename the binary to `fairy-stockfish.exe` (on Windows) or `fairy-stockfish` (on Linux/macOS)
4. Place the binary in this directory

## Configuration

The config.yml file is already configured to use these engines:
- `standard`: Uses latest sf (already included)
- `variants`: General variant engine using Fairy-Stockfish
- `chess960`: Chess960-specific engine with UCI_Chess960 enabled
- `atomic`: Atomic chess engine with UCI_Variant set to atomic
- `horde`: Horde chess engine with UCI_Variant set to horde

Make sure to adjust the engine paths and options in config.yml according to your system and preferences.
