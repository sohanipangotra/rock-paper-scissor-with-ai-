from flask import Flask, render_template, Response, request, jsonify
import cv2
import time
import numpy as np
from detector import get_gesture
from game import Game

app = Flask(__name__)
game = Game()
game.set_difficulty("easy")

# Game state
state = "waiting"
countdown_start = 0
COUNTDOWN_SEC = 3
result_shown_at = 0
RESULT_DISPLAY_SEC = 2.5
captured_gesture = None

# Global capture
cap = cv2.VideoCapture(0)

def gen_frames():
    global state, countdown_start, result_shown_at, captured_gesture
    
    while True:
        success, frame = cap.read()
        if not success:
            break
            
        # Mirror flip
        frame = cv2.flip(frame, 1)
        
        # Gesture detection
        gesture, frame = get_gesture(frame)
        
        # Game State Logic (adapted from main.py)
        if state == "waiting":
            # Hand detection hint is already in frame from detector.py (optional)
            pass
            
        elif state == "countdown":
            elapsed = time.time() - countdown_start
            remaining = COUNTDOWN_SEC - int(elapsed)
            
            if remaining > 0:
                # Draw countdown on frame
                h, w = frame.shape[:2]
                cv2.putText(frame, str(remaining), (w//2-40, h//2+40), 
                            cv2.FONT_HERSHEY_DUPLEX, 6, (255, 255, 255), 10)
            else:
                captured_gesture = gesture
                # Trigger round only if move is valid
                if captured_gesture in ("Rock", "Paper", "Scissors"):
                    game.play_round(captured_gesture)
                    state = "result"
                    result_shown_at = time.time()
                else:
                    # If gesture is Unknown or None, still go to result state but with an "Error" flag
                    # Our game.py doesn't have an error state, so we just set last_result to None
                    game.last_player_move = captured_gesture if captured_gesture else "None"
                    game.last_result = "error"
                    state = "result"
                    result_shown_at = time.time()
                    
        elif state == "result":
            info = game.get_last_round()
            h, w = frame.shape[:2]
            
            if info['result'] == "error":
                # Handle 'Unknown' gestures more gracefully
                if info['player'] == "Unknown" or info['player'] == "None":
                    res_text = "GESTURE NOT RECOGNIZED"
                else:
                    res_text = "ERROR IN GAME LOGIC" # Fallback for other errors
                color = (0, 0, 255) # Red for error
            else:
                res_text = f"{info['result'].upper()}! {info['player']} vs {info['ai']}"
                color = (0, 255, 255) # Yellow for normal results
                
            cv2.putText(frame, res_text, (50, h-80), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            
            if time.time() - result_shown_at > RESULT_DISPLAY_SEC:
                state = "waiting"
        
        # Encode for streaming
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/action', methods=['POST'])
def action():
    global state, countdown_start
    data = request.json
    cmd = data.get('cmd')
    
    if cmd == 'start' and state == 'waiting':
        state = 'countdown'
        countdown_start = time.time()
        return jsonify({"status": "countdown started"})
        
    elif cmd in ['1', '2', '3']:
        difficulties = {'1': 'easy', '2': 'medium', '3': 'hard'}
        game.set_difficulty(difficulties[cmd])
        return jsonify({"status": f"difficulty set to {difficulties[cmd]}"})
        
    return jsonify({"status": "ignored", "state": state})

@app.route('/game_info')
def game_info():
    score = game.get_score()
    last_round = game.get_last_round()
    return jsonify({
        "score": score,
        "last_round": last_round,
        "state": state,
        "difficulty": game.ai.difficulty
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
