import numpy as np
import cv2

def debug_flow():
    img1 = np.zeros((100, 100, 3), dtype=np.uint8)
    for i in range(0, 100, 10):
        img1[:, i:i+5] = 255
    img2 = np.roll(img1, 3, axis=1)

    prev_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    curr_gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    print("prev_gray mean:", np.mean(prev_gray))
    print("curr_gray mean:", np.mean(curr_gray))

    try:
        flow = cv2.calcOpticalFlowFarneback(
            prev_gray, curr_gray, None, 
            pyr_scale=0.5, levels=3, winsize=15, 
            iterations=3, poly_n=5, poly_sigma=1.2, flags=0
        )
        magnitude, angle = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        print("max magnitude:", np.max(magnitude))
        print("mean magnitude:", np.mean(magnitude))
        print("first flow pixel:", flow[50, 50])
    except Exception as e:
        print("Farneback failed:", e)

if __name__ == "__main__":
    debug_flow()
