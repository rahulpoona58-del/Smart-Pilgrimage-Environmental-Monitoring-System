# test_setup.py
# First Python Script: Verifies installed dependencies and GPU status.

import sys

# 1. Print current Python version
print("=========================================")
print("System Diagnostics")
print("=========================================")
print(f"Python Version: {sys.version}")

# 2. Check and print OpenCV version
try:
    import cv2
    print(f"OpenCV Version: {cv2.__version__}")
except ImportError:
    print("Error: OpenCV is not installed.")

# 3. Check and print Ultralytics YOLOv8 version
try:
    import ultralytics
    print(f"Ultralytics YOLO Version: {ultralytics.__version__}")
except ImportError:
    print("Error: Ultralytics is not installed.")

# 4. Check and print EasyOCR version
try:
    import easyocr
    print("EasyOCR: Successfully imported.")
except ImportError:
    print("Error: EasyOCR is not installed.")

# 5. Verify PyTorch and CUDA (GPU acceleration) status
try:
    import torch
    print(f"PyTorch Version: {torch.__version__}")
    cuda_available = torch.cuda.is_available()
    print(f"CUDA GPU Acceleration Available: {cuda_available}")
    if cuda_available:
        print(f"Active GPU Device Name: {torch.cuda.get_device_name(0)}")
except ImportError:
    print("Error: PyTorch is not installed.")

print("=========================================")
