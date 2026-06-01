# test_opencv.py
# First OpenCV Program: Validates image matrix manipulation and filtering.

import cv2
import numpy as np

def run_opencv_test():
    # 1. Create a black image matrix (height: 480px, width: 640px, channels: 3 (BGR))
    # np.zeros constructs a matrix filled with 0s (representing solid black pixels)
    img = np.zeros((480, 640, 3), dtype=np.uint8)

    # 2. Draw a rectangle (represents a simulated license plate bounding box)
    # cv2.rectangle syntax: image, start_point(x,y), end_point(x,y), color(B,G,R), thickness
    # Here, color is (0, 240, 255) -> Cyan. Thickness is 3 pixels.
    cv2.rectangle(img, (150, 180), (490, 300), (0, 240, 255), 3)

    # 3. Draw a circle (represents an optical tracking focal marker)
    # cv2.circle syntax: image, center_coordinates(x,y), radius, color, thickness (-1 fills the circle)
    # Color is (16, 185, 129) -> Emerald Green.
    cv2.circle(img, (320, 240), 12, (16, 185, 129), -1)

    # 4. Write mock license text on the canvas
    # cv2.putText syntax: image, text, origin_point(x,y), font_type, font_scale, color, thickness
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, "UK07TA1234", (180, 260), font, 1.5, (255, 255, 255), 4)

    # 5. Apply a bilateral filter (noise-reduction filter that preserves sharp character borders)
    # Syntax: source, diameter, sigmaColor, sigmaSpace
    filtered_img = cv2.bilateralFilter(img, 9, 75, 75)

    # 6. Save the final image to a local file
    # cv2.imwrite writes the matrix to a standard JPG file format
    output_filename = "test_output.jpg"
    success = cv2.imwrite(output_filename, filtered_img)

    if success:
        print("=========================================")
        print("OpenCV Test Result")
        print("=========================================")
        print(f"Successfully processed image size: {img.shape}")
        print(f"Output saved to: {output_filename}")
        print("Verification: OpenCV operations are active.")
        print("=========================================")
    else:
        print("Error: Failed to write test image output.")

if __name__ == "__main__":
    run_opencv_test()
