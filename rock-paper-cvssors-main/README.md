# RockPaperCVssors

A hand gesture based Rock Paper Scissors game built with Python, OpenCV, and CVZone. Show your hand to the camera and play against an AI with three difficulty levels.

---

## How It Works

The camera detects your hand using MediaPipe landmarks via CVZone. It reads which fingers are up and maps the pattern to a gesture:

- Rock: no fingers up
- Paper: all five fingers up
- Scissors: index and middle fingers up

---

## Project Structure

```
RockPaperCVssors/
├── main.py          # entry point and game loop
├── detector.py      # hand detection and gesture mapping
├── ai.py            # AI logic for all three difficulty modes
├── game.py          # scoring and win/loss/draw logic
└── requirements.txt
```

---

## Requirements

- Python 3.9 to 3.11
- Webcam

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Game

```bash
python main.py
```

Press Q to quit.

---

## Difficulty Modes

Easy: AI picks randomly every round.

Medium: AI tracks your last 5 moves and counters your most frequent gesture about half the time.

Hard: AI tracks your full session history and almost always counters your most played gesture.

---

## Controls

- Space: start a round
- 1 / 2 / 3: select Easy / Medium / Hard mode
- Q: quit

---

## Gesture Reference

| Gesture  | Fingers Up            |
| -------- | --------------------- |
| Rock     | None                  |
| Paper    | All five              |
| Scissors | Index and middle only |
