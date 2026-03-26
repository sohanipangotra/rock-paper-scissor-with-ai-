import cv2
import time
import numpy as np
from detector import get_gesture
from game import Game

game = Game()
game.set_difficulty("easy")  # default difficulty

# states: "waiting", "countdown", "result"
state = "waiting"
countdown_start = None
COUNTDOWN_SEC = 3
result_shown_at = None
RESULT_DISPLAY_SEC = 2.5

captured_gesture = None

MOVE_EMOJI = {"Rock": "ROCK", "Paper": "PAPER", "Scissors": "SCISSORS"}
DIFFICULTY_COLOR = {
    "easy": (50, 200, 100),
    "medium": (50, 170, 255),
    "hard": (50, 50, 255),
}


def draw_overlay(img, x1, y1, x2, y2, color, alpha=0.55):
    """Blend a colored rectangle over the image."""
    overlay = img.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)


def draw_text_shadow(
    img, text, pos, font, scale, color, thickness, shadow_color=(0, 0, 0)
):
    ox, oy = pos
    cv2.putText(
        img,
        text,
        (ox + 2, oy + 2),
        font,
        scale,
        shadow_color,
        thickness + 1,
        cv2.LINE_AA,
    )
    cv2.putText(img, text, (ox, oy), font, scale, color, thickness, cv2.LINE_AA)


def draw_score_hud(img, score):
    h, w = img.shape[:2]
    panel_h = 50
    draw_overlay(img, 0, 0, w, panel_h, (20, 20, 20), alpha=0.65)

    # Wins
    draw_text_shadow(
        img,
        f"W  {score['wins']}",
        (14, 35),
        cv2.FONT_HERSHEY_DUPLEX,
        0.75,
        (60, 220, 100),
        2,
    )
    # Losses
    score_w, _ = cv2.getTextSize(
        f"W  {score['wins']}", cv2.FONT_HERSHEY_DUPLEX, 0.75, 2
    )[0]
    draw_text_shadow(
        img,
        f"L  {score['losses']}",
        (14 + score_w + 30, 35),
        cv2.FONT_HERSHEY_DUPLEX,
        0.75,
        (60, 80, 255),
        2,
    )
    # Draws
    score_d, _ = cv2.getTextSize(
        f"L  {score['losses']}", cv2.FONT_HERSHEY_DUPLEX, 0.75, 2
    )[0]
    draw_text_shadow(
        img,
        f"D  {score['draws']}",
        (14 + score_w + 30 + score_d + 30, 35),
        cv2.FONT_HERSHEY_DUPLEX,
        0.75,
        (200, 200, 200),
        2,
    )


def draw_difficulty_badge(img, difficulty):
    h, w = img.shape[:2]
    color = DIFFICULTY_COLOR.get(difficulty.lower(), (180, 180, 180))
    label = difficulty.upper()
    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
    pad_x, pad_y = 12, 8
    rx2 = w - 12
    ry2 = 44
    rx1 = rx2 - tw - pad_x * 2
    ry1 = 10
    # pill bg
    draw_overlay(img, rx1, ry1, rx2, ry2, color, alpha=0.4)
    cv2.rectangle(img, (rx1, ry1), (rx2, ry2), color, 2)
    draw_text_shadow(
        img, label, (rx1 + pad_x, ry2 - pad_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2
    )


def draw_controls_bar(img):
    h, w = img.shape[:2]
    bar_h = 36
    draw_overlay(img, 0, h - bar_h, w, h, (20, 20, 20), alpha=0.70)
    controls = "SPACE: Play    1: Easy    2: Medium    3: Hard    Q: Quit"
    (tw, _), _ = cv2.getTextSize(controls, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
    cx = (w - tw) // 2
    cv2.putText(
        img,
        controls,
        (cx, h - 11),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (180, 180, 180),
        1,
        cv2.LINE_AA,
    )


def draw_waiting(img, gesture):
    h, w = img.shape[:2]

    # Instruction card
    card_y1, card_y2 = 58, 185
    draw_overlay(img, 10, card_y1, w - 10, card_y2, (15, 15, 30), alpha=0.60)
    cv2.rectangle(img, (10, card_y1), (w - 10, card_y2), (80, 80, 200), 1)

    # "Show your hand" label
    cv2.putText(
        img,
        "Show your hand!",
        (30, card_y1 + 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (160, 160, 255),
        2,
        cv2.LINE_AA,
    )

    # Detected gesture
    if gesture and gesture not in ("Unknown", "No hand"):
        color = (60, 230, 120)
        label = gesture.upper()
    else:
        color = (100, 100, 100)
        label = "NO HAND DETECTED"

    draw_text_shadow(
        img, label, (30, card_y1 + 90), cv2.FONT_HERSHEY_DUPLEX, 1.3, color, 3
    )

    # Press space hint
    cv2.putText(
        img,
        "Press  SPACE  to start round",
        (30, card_y2 - 14),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (200, 200, 200),
        1,
        cv2.LINE_AA,
    )


def draw_countdown(img, remaining):
    h, w = img.shape[:2]

    # Darken the frame slightly
    draw_overlay(img, 0, 0, w, h, (0, 0, 0), alpha=0.25)

    # Large countdown number
    digit = str(remaining)
    font = cv2.FONT_HERSHEY_DUPLEX
    scale = 7.0
    thick = 14
    (tw, th), _ = cv2.getTextSize(digit, font, scale, thick)
    cx = (w - tw) // 2
    cy = (h + th) // 2

    # Glow ring
    glow_colors = [(0, 200, 255), (0, 150, 200), (0, 100, 150)]
    for i, gc in enumerate(glow_colors):
        cv2.putText(
            img, digit, (cx, cy), font, scale, gc, thick + 8 - i * 3, cv2.LINE_AA
        )

    # Core number
    cv2.putText(img, digit, (cx, cy), font, scale, (255, 255, 255), thick, cv2.LINE_AA)

    # "Get ready!" hint
    hint = "Get ready!"
    (hw, _), _ = cv2.getTextSize(hint, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)
    cv2.putText(
        img,
        hint,
        ((w - hw) // 2, cy + 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (200, 200, 200),
        2,
        cv2.LINE_AA,
    )


def draw_result(img, info):
    h, w = img.shape[:2]

    result = info["result"]
    if result == "error":
        meta = {"label": "NOT RECOGNIZED", "color": (60, 60, 240), "bg": (20, 10, 60)}
    else:
        result_meta = {
            "win": {"label": "YOU WIN!", "color": (40, 210, 80), "bg": (0, 60, 20)},
            "loss": {"label": "YOU LOSE", "color": (60, 60, 240), "bg": (20, 10, 60)},
            "draw": {"label": "DRAW", "color": (20, 200, 255), "bg": (0, 40, 60)},
        }
        meta = result_meta.get(
            result, {"label": result.upper(), "color": (200, 200, 200), "bg": (30, 30, 30)}
        )

    # Full-width result banner
    banner_y1, banner_y2 = 56, 210
    draw_overlay(img, 0, banner_y1, w, banner_y2, meta["bg"], alpha=0.75)
    cv2.rectangle(img, (0, banner_y1), (w, banner_y2), meta["color"], 2)

    # Result label
    label = meta["label"]
    font = cv2.FONT_HERSHEY_DUPLEX
    scale = 2.0 if result == "error" else 2.5
    (lw, lh), _ = cv2.getTextSize(label, font, scale, 5)
    draw_text_shadow(
        img, label, ((w - lw) // 2, banner_y1 + 80), font, scale, meta["color"], 5
    )

    if result != "error":
        # Moves display
        player_txt = f"You:  {info['player'].upper()}"
        ai_txt = f"AI:   {info['ai'].upper()}"

        draw_text_shadow(
            img,
            player_txt,
            (30, banner_y1 + 130),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.85,
            (220, 220, 220),
            2,
        )
        draw_text_shadow(
            img,
            ai_txt,
            (30, banner_y1 + 165),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.85,
            (180, 180, 180),
            2,
        )


cap = cv2.VideoCapture(0)
cv2.namedWindow("RockPaperCVssors", cv2.WINDOW_NORMAL)

# Gently resize window if screen allows
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)

while True:
    success, img = cap.read()
    if not success:
        break

    # Apply mirror flip for better UX (mirror effect)
    img = cv2.flip(img, 1)

    gesture, img = get_gesture(img)

    if state == "waiting":
        draw_waiting(img, gesture)

    elif state == "countdown":
        elapsed = time.time() - countdown_start
        remaining = COUNTDOWN_SEC - int(elapsed)

        if remaining > 0:
            draw_countdown(img, remaining)
        else:
            captured_gesture = gesture
            if captured_gesture in ("Rock", "Paper", "Scissors"):
                result = game.play_round(captured_gesture)
                state = "result"
                result_shown_at = time.time()
            else:
                # If gesture is Unknown or None, show error message
                game.last_player_move = captured_gesture if captured_gesture else "None"
                game.last_result = "error"
                state = "result"
                result_shown_at = time.time()

    elif state == "result":
        info = game.get_last_round()
        draw_result(img, info)

        if time.time() - result_shown_at > RESULT_DISPLAY_SEC:
            state = "waiting"

    draw_score_hud(img, game.get_score())
    draw_difficulty_badge(img, game.ai.difficulty)
    draw_controls_bar(img)

    cv2.imshow("RockPaperCVssors", img)

    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break
    elif key == ord(" ") and state == "waiting":
        state = "countdown"
        countdown_start = time.time()
    elif key == ord("1"):
        game.set_difficulty("easy")
    elif key == ord("2"):
        game.set_difficulty("medium")
    elif key == ord("3"):
        game.set_difficulty("hard")

cap.release()
cv2.destroyAllWindows()
