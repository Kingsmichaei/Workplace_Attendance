import cv2
import numpy as np
import base64


class FacialRecognitionEngine:

    @staticmethod
    def base64_to_image(base64_string):
        try:
            format, imgstr = base64_string.split(';base64,')
            image_bytes = base64.b64decode(imgstr)
            np_array = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
            return image
        except Exception:
            return None

    @staticmethod
    def get_face_encodings_from_image(image):
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) == 0:
            return []

        encodings = []

        for (x, y, w, h) in faces:
            face = gray[y:y+h, x:x+w]
            face = cv2.resize(face, (200, 200))
            encodings.append(face)

        return encodings




@staticmethod
def verify_face(known_faces, captured_face, target_label=0):
    """
    Train recognizer on ALL known faces.
    Verify captured face matches ONLY the target user.
    
    Args:
        known_faces: list of ALL registered face encodings in system
        captured_face: the face image to verify
        target_label: index of the target user in known_faces list
    """
    if not known_faces:
        return False, 999

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    labels = list(range(len(known_faces)))
    recognizer.train(known_faces, np.array(labels))
    predicted_label, confidence = recognizer.predict(captured_face)

    # BOTH conditions must be true:
    # 1. Predicted face must match target user specifically
    # 2. Confidence must be below strict threshold
    is_match = (predicted_label == target_label) and (confidence < 70)
    return is_match, confidence