# Facial Recognition Integration Guide

## Overview

This Django workplace attendance system now includes integrated facial recognition technology for secure and convenient attendance tracking. Employees can register their faces and use facial recognition for clock-in/clock-out operations, as well as for alternative login authentication.

## Features

### 1. **Facial Registration**
- Users can register their facial data from the dashboard
- A dedicated registration page with live camera feed
- Supports single or multiple face captures for better accuracy
- Clear feedback on registration status

### 2. **Facial Clock In/Out**
- Use facial recognition instead of manual clock-in
- Live camera feed for face verification
- Real-time feedback on success or failure
- Attendance records show which method was used (manual or facial)

### 3. **Facial Login**
- Alternative login method using facial recognition
- Accessible from the login page
- Requires username entry for security
- Seamless integration with existing authentication

## Installation

### 1. Install Required Dependencies

```bash
pip install -r requirements.txt
```

**Key packages:**
- `face-recognition`: Main facial recognition library
- `opencv-python`: Computer vision library
- `Pillow`: Image processing
- `numpy`: Numerical computations
- `dlib`: Machine learning library

### 2. Apply Database Migrations

```bash
python manage.py migrate
```

This will:
- Create the `FaceData` model for storing facial encodings
- Add `clock_in_method` and `clock_out_method` fields to `Attendance` model

### 3. Run Development Server

```bash
python manage.py runserver
```

## How to Use

### For Employees

#### Registering Your Face
1. Log in to the dashboard
2. Click "Register Face" button in the Facial Recognition Attendance section
3. Allow camera access when prompted
4. Position your face in the center of the camera frame
5. Ensure good lighting (natural light is best)
6. Click "Capture Photo"
7. Review the captured image
8. Click "Confirm & Register" to save your facial data

**Tips for best results:**
- Use good natural lighting
- Remove or adjust glasses if they reflect light
- Look directly at the camera
- Keep your face centered in the frame
- Avoid shadows on your face

#### Using Facial Clock In/Out
1. Go to the dashboard
2. Click "Facial Clock In" button
3. Position your face in the camera frame
4. Click "Verify Face"
5. Wait for verification (usually less than 2 seconds)
6. You'll see a success message and your attendance will be recorded

#### Logging In with Facial Recognition
1. On the login page, click the "Facial Recognition" tab
2. Enter your username
3. Click "Start Camera"
4. Position your face in the camera frame
5. Click "Verify Face"
6. You'll be logged in automatically if recognized

### For Administrators

#### Viewing Facial Data
1. Go to Django Admin (/admin/)
2. Navigate to "Face Data" section
3. View which employees have registered faces
4. Monitor registration dates
5. See face registration status at a glance

#### Attendance Reports
The attendance records now show the method used:
- **Manual**: Traditional clock in/out
- **Facial**: Facial recognition based clock in/out

## Technical Details

### FaceData Model

The `FaceData` model stores:
- `user`: ForeignKey to User (one-to-one)
- `facial_encodings`: Stores 128-dimensional facial encodings as JSON
- `face_registered`: Boolean flag indicating registration status
- `registered_at`: Timestamp of registration
- `updated_at`: Timestamp of last update

### Facial Encodings

Facial encodings are:
- Generated using the `face_recognition` library
- 128-dimensional NumPy arrays
- Serialized to JSON for storage
- Compared using Euclidean distance
- Default tolerance: 0.6 (adjustable in `facial_recognition.py`)

### API Endpoints

#### `/attendance/api/capture-face-registration/` (POST)
Captures and stores facial encoding during registration
- **Input**: Base64 encoded image
- **Output**: JSON response with success status

#### `/attendance/api/facial-clock/` (POST)
Handles facial recognition for clock in/out
- **Input**: Base64 encoded image, action (clock_in/clock_out)
- **Output**: JSON response with success status and attendance details

#### `/attendance/api/facial-login/` (POST)
Alternative login using facial recognition
- **Input**: Base64 encoded image, username
- **Output**: JSON response with redirect URL on success

## Security Considerations

### Best Practices

1. **Facial Data Storage**
   - Encodings are stored locally in the database
   - No face images are permanently stored
   - Encodings cannot be reverse-engineered to reconstruct faces

2. **Access Control**
   - Facial registration requires logged-in status
   - Facial login requires username entry
   - All operations are HTTPS-recommended in production

3. **Accuracy**
   - Tolerance level set to 0.6 (balanced security/usability)
   - Can be adjusted in `facial_recognition.py`
   - Multiple registrations improve accuracy

### Privacy Notes

- Only facial encodings (mathematical representations) are stored
- Original face images are not saved
- Employees have full control over their facial data
- Facial data is tied to user accounts
- Can be deleted by administrators if needed
- Follows GDPR best practices for biometric data

## Troubleshooting

### Camera Not Accessing

**Problem**: Browser asks for permission but camera doesn't work

**Solutions**:
- Check browser permissions (Settings → Privacy → Camera)
- Ensure HTTPS in production (camera access requires secure context)
- Try a different browser
- Check if camera is already in use by another application

### Face Not Recognized

**Problem**: Facial recognition fails even though face is registered

**Possible causes**:
1. Poor lighting conditions
2. Significant change in appearance (new glasses, facial hair, etc.)
3. Face at wrong angle (look directly at camera)
4. Multiple faces in frame
5. Registration image was poor quality

**Solutions**:
- Register again with better lighting
- Ensure face is centered and looking at camera
- Remove other people from the frame
- Try registering multiple times from different angles

### No Face Detected

**Problem**: System says "No face detected in the image"

**Solutions**:
- Ensure your face is clearly visible
- Move closer to camera
- Improve lighting
- Remove sunglasses or hats
- Avoid shadows on your face

### Registration Success But Verification Fails

**Problem**: Registered successfully but can't verify during clock in/out

**Solutions**:
- Register again in similar lighting conditions as where you'll clock in
- Register multiple times from different angles
- Ensure you're in the same location with same lighting for consistency

## Adjusting Settings

### Tolerance Level

To adjust the facial recognition strictness, edit `facial_recognition.py`:

```python
TOLERANCE = 0.6  # Lower = stricter, Higher = more lenient
```

- Default: 0.6
- Stricter: 0.4-0.5
- More lenient: 0.7-0.8

### Multiple Registrations

For better accuracy, users can register multiple times:
1. Each new registration updates the stored encodings
2. Multiple face captures improve matching consistency
3. Different angles and lighting conditions are recommended

## Performance Considerations

- Facial recognition is performed client-side (in browser)
- Server processes the image and performs the verification
- Processing time: ~1-2 seconds per face
- Database size impact: ~2KB per registered user

## Browser Compatibility

**Supported Browsers**:
- Chrome/Chromium 50+
- Firefox 55+
- Safari 11+
- Edge 79+

**Requirements**:
- Camera access permission
- JavaScript enabled
- HTTPS (recommended in production)

## Database Backup

The `FaceData` model stores facial encodings. When backing up:
- Include the `attendance_facedata` table
- Encodings are JSON-serialized text
- No special binary format
- Standard database backup tools work fine

## Future Enhancements

Potential improvements:
1. Multi-face matching (for group clock-in)
2. Liveness detection (to prevent spoofing with photos)
3. Facial attribute recognition (age estimation, emotion detection)
4. Batch facial registration
5. Mobile app support
6. Real-time attendance dashboard with facial verification

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review browser console for JavaScript errors
3. Check Django logs for backend errors
4. Verify camera permissions and browser compatibility
5. Test with different lighting conditions

## License

This facial recognition integration uses:
- `face_recognition` library (MIT License)
- OpenCV (Apache 2 License)
- dlib (Boost Software License)

All integrated within Django's BSD License framework.

---

**Last Updated**: February 2026
**Version**: 1.0
