COIN RUNNER PRO

Features:
- Animated cartoon runner drawn with Pygame shapes; no external image files required
- Start screen, jump, double jump, slide, coin collection, score, game over, restart
- Power-ups: magnet, shield, double coins
- Best score saved in coin_runner_save.json
- Generated sound effects (no external audio files required)
- Scrolling scenery, particles, gradually increasing difficulty, pause screen

WINDOWS SETUP
1. Install Python 3.13 64-bit from https://www.python.org/downloads/release/python-31316/
2. In setup, tick Add Python to PATH if offered.
3. Open PowerShell in this folder.
4. Run: py -3.13 -m pip install pygame==2.6.1
5. Run: py -3.13 coin_runner_pro.py

CONTROLS
SPACE / UP / W: jump (double jump supported)
DOWN / S: slide
P: pause/resume
ESC: pause during game; quit from menu/game-over
R: restart during play or after game over
ENTER / SPACE: start/restart

The save file is created beside the script. If audio is unavailable, the game still runs silently.
