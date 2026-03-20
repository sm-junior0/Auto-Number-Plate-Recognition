import cv2
import numpy as np
import sys

def create_plate():
    # Create white canvas
    img = np.ones((140, 450, 3), dtype=np.uint8) * 255
    
    # Draw text: "ABC123D" to match regex [A-Z]{3}[0-9]{3}[A-Z]
    text = "ABC 123 D"
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 2
    thickness = 6
    
    # Get text size to center it
    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
    text_x = (img.shape[1] - text_size[0]) // 2
    text_y = (img.shape[0] + text_size[1]) // 2
    
    cv2.putText(img, text, (text_x, text_y), font, font_scale, (0, 0, 0), thickness)
    
    # Put some padding to simulate the rest of the car
    car_img = np.ones((600, 800, 3), dtype=np.uint8) * 128
    
    plate_x = (car_img.shape[1] - img.shape[1]) // 2
    plate_y = (car_img.shape[0] - img.shape[0]) // 2
    
    # Draw black border around plate
    border_thickness = 4
    cv2.rectangle(car_img, 
                  (plate_x - border_thickness, plate_y - border_thickness), 
                  (plate_x + img.shape[1] + border_thickness, plate_y + img.shape[0] + border_thickness), 
                  (0, 0, 0), -1)
    
    car_img[plate_y:plate_y+img.shape[0], plate_x:plate_x+img.shape[1]] = img
    
    cv2.imwrite("data/plates/dummy_plate.jpg", car_img)
    print("Created synthetic plate image at data/plates/dummy_plate.jpg")

if __name__ == "__main__":
    create_plate()
