import cv2

def test_cam():
    print("Scanning for cameras...")
    for index in range(5):
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                print(f"Found camera at index {index}")
            else:
                print(f"Camera at index {index} opened but returned no frame")
            cap.release()
        else:
            print(f"No camera at index {index}")

if __name__ == "__main__":
    test_cam()
