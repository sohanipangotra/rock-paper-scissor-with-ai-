import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np

# Load Hand Landmarker
base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1,
    min_hand_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
detector = vision.HandLandmarker.create_from_options(options)

def get_gesture(img):
    """
    Takes a frame, detects hand, returns (gesture, img)
    gesture is "Rock", "Paper", "Scissors", "Unknown", or None (no hand)
    Using MediaPipe Tasks API for compatibility with newer Python versions.
    """
    # Convert image to RGB for MediaPipe (img is already flipped in main.py)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
    
    # Detect landmarks
    result = detector.detect(mp_image)
    
    if not result.hand_landmarks:
        return None, img
    
    # Process only the first hand
    hand_landmarks = result.hand_landmarks[0]
    hand_type = result.handedness[0][0].category_name # "Left" or "Right"
    
    # Convert to list of [x, y, z] in pixels
    h, w, _ = img.shape
    lm_list = []
    for lm in hand_landmarks:
        lm_list.append([int(lm.x * w), int(lm.y * h), lm.z])
    
    # Determine which fingers are up
    fingers = []
    
    # Thumb logic
    if hand_type == "Right":
        if lm_list[4][0] > lm_list[3][0]:
            fingers.append(1)
        else:
            fingers.append(0)
    else:
        if lm_list[4][0] < lm_list[3][0]:
            fingers.append(1)
        else:
            fingers.append(0)
            
    # 4 Fingers logic: compare y-coordinate of tip and dip joint
    tip_ids = [8, 12, 16, 20]
    for tid in tip_ids:
        if lm_list[tid][1] < lm_list[tid - 2][1]:
            fingers.append(1)
        else:
            fingers.append(0)
            
    # Robust Pattern Matching Logic:
    # 1. Scissors: Index and Middle are up, Ring and Pinky are down (mostly).
    # 2. Paper: All or most fingers are up.
    # 3. Rock: All main 4 fingers are down.
    
    thumb, index, mid, ring, pinky = fingers
    
    if index == 1 and mid == 1:
        if ring == 0 and pinky == 0:
            gesture = "Scissors"
        elif ring == 1 or pinky == 1:
            gesture = "Paper"
        else:
            gesture = "Unknown"
    elif index == 0 and mid == 0 and ring == 0 and pinky == 0:
        gesture = "Rock"
    elif index == 1 or mid == 1 or ring == 1 or pinky == 1:
        # If at least 3 fingers are up, call it Paper
        if (index + mid + ring + pinky) >= 3:
            gesture = "Paper"
        else:
            gesture = "Unknown"
    else:
        gesture = "Unknown"
    
    # Visual feedback: simplified skeletons
    for i, lm in enumerate(lm_list):
        cv2.circle(img, (lm[0], lm[1]), 3, (120, 255, 120), -1)
        
    return gesture, img
