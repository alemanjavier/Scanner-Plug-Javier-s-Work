from PyQt5.QtWidgets import QWidget
from PyQt5 import uic
#this file should make the elements in the "settings_tabWidget" functional
import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QVBoxLayout, QWidget, QSlider, QLineEdit, QHBoxLayout, QPushButton, QRadioButton, QMessageBox, QFileDialog, QTabWidget, QLabel, QComboBox, QCheckBox,QSizePolicy
from PyQt5 import uic, QtWidgets
import serial.tools.list_ports
import time
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPainter, QBrush, QPen
from PyQt5 import QtTest

import argparse
import json
import os

import cv2
import numpy as np
import itertools
# start by importing the necessary packages
import matplotlib.pyplot as plt
import json
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtGui import QPixmap, QImage
import pyautogui
import sys
from PyQt5.QtWidgets import QDialog, QMainWindow, QApplication, QMainWindow, QVBoxLayout, QWidget, QSlider,QLineEdit, QHBoxLayout, QPushButton, QRadioButton, QMessageBox, QFileDialog, QTabWidget, QLabel, QComboBox,QCheckBox
from PyQt5 import uic
import serial.tools.list_ports
import time
#from moving_fun import fun_testEachAxisMoveLoop
from PyQt5 import QtTest

import sys
import time


from window_interaction_handler import WindowInteractionHandler
from motion_controller import MotionController
import glob
import random

class AiTab(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("ai_tab.ui", self)
        
        # Store the training data folder path
        self.training_data_folder = None
        
        # Connect buttons
        self.saving_folder_4.clicked.connect(self.train_valid)
        self.saving_folder_5.clicked.connect(self.train_invalid)
        self.saving_folder_6.clicked.connect(self.set_save_folder)
        self.saving_folder_7.clicked.connect(self.process_and_label_data)
    
    def set_save_folder(self):
        """Set the folder where training images are stored"""
        folder = QFileDialog.getExistingDirectory(self, "Select Training Images Folder")
        if folder:
            self.training_data_folder = folder
            QMessageBox.information(self, "Folder Selected", f"Training folder set to:\n{folder}")
    
    def train_valid(self):
        """Run valid_flake_data when train valid button is clicked"""
        folder = self.training_data_folder
        if not folder:
            folder = QFileDialog.getExistingDirectory(self, "Select Folder Containing Training Images")
            if not folder:
                return
            self.training_data_folder = folder
        
        # Run the valid_flake_data function
        valid_flake_data(folder=folder)
        QMessageBox.information(self, "Complete", "Valid flake data collection completed!\nData saved to datapoints/true_data_points.json")
    
    def train_invalid(self):
        """Run invalid_area_data when train invalid button is clicked"""
        folder = self.training_data_folder
        if not folder:
            folder = QFileDialog.getExistingDirectory(self, "Select Folder Containing Training Images")
            if not folder:
                return
            self.training_data_folder = folder
        
        # Run the invalid_area_data function
        invalid_area_data(folder=folder)
        QMessageBox.information(self, "Complete", "Invalid area data collection completed!\nData saved to datapoints/false_data_points.json")
    
    def process_and_label_data(self):
        """Process collected data: add labels, combine and shuffle"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        datapoints_dir = os.path.join(script_dir, "datapoints")
        
        true_data_points_path = os.path.join(datapoints_dir, "true_data_points.json")
        false_data_points_path = os.path.join(datapoints_dir, "false_data_points.json")
        true_labeled_path = os.path.join(datapoints_dir, "labeled_true_data_points.json")
        false_labeled_path = os.path.join(datapoints_dir, "labeled_false_data_points.json")
        final_data_path = os.path.join(script_dir, "final_data.json")
        
        # Check if input files exist
        if not os.path.exists(true_data_points_path):
            QMessageBox.warning(self, "Missing Data", 
                              f"true_data_points.json not found.\nPlease run 'train valid' first.")
            return
        
        if not os.path.exists(false_data_points_path):
            QMessageBox.warning(self, "Missing Data", 
                              f"false_data_points.json not found.\nPlease run 'train invalid' first.")
            return
        
        try:
            # Add labels
            add_label_to_data(true_data_points_path, 1, output_path=true_labeled_path)
            add_label_to_data(false_data_points_path, 0, output_path=false_labeled_path)
            
            # Combine and shuffle
            combine_and_shuffle(true_labeled_path, false_labeled_path, final_data_path)
            
            QMessageBox.information(self, "Success", 
                                  f"Data processed successfully!\n\n"
                                  f"Labeled valid data: {true_labeled_path}\n"
                                  f"Labeled invalid data: {false_labeled_path}\n"
                                  f"Final combined data: {final_data_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error processing data:\n{str(e)}")


def valid_flake_data(folder=None):
    """Collect valid flake data by clicking on flakes in images"""
    import json
    import cv2
    import os
    import glob
    import numpy as np

    # Ask for the folder containing images
    if not folder:
        folder = input("Enter the path to the folder containing images: ").strip()

    # Gather image paths
    image_extensions = ["*.jpg", "*.jpeg", "*.png", "*.bmp", "*.tiff"]
    image_paths = []
    for ext in image_extensions:
        image_paths.extend(glob.glob(os.path.join(folder, ext)))
    image_paths.sort()
    if not image_paths:
        print("No images found in the provided folder.")
        return

    saved_data = {}
    current_image_index = 0
    current_clicks = []
    original_image = None
    display_image = None

    # Zoom / pan state
    zoom_scale = 1.0
    zoom_center = None
    ZOOM_STEP = 1.25
    PAN_STEP = 50

    def draw_overlay(img, filename):
        overlay = img.copy()
        cv2.putText(overlay, filename, (10, overlay.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        if filename in saved_data and saved_data[filename]:
            text = f"Saved sets: {len(saved_data[filename])}"
            cv2.putText(overlay, text, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        return overlay

    def get_display_image():
        nonlocal zoom_center
        h, w = original_image.shape[:2]
        if zoom_center is None:
            zoom_center = (w // 2, h // 2)

        win_w, win_h = int(w / zoom_scale), int(h / zoom_scale)
        cx, cy = zoom_center
        x1 = max(0, cx - win_w // 2)
        y1 = max(0, cy - win_h // 2)
        x2 = min(w, x1 + win_w)
        y2 = min(h, y1 + win_h)

        cropped = original_image[y1:y2, x1:x2]
        resized = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)
        disp = draw_overlay(resized, os.path.basename(image_paths[current_image_index]))
        for (x, y) in current_clicks:
            cv2.circle(disp, (x, y), 5, (0, 255, 0), -1)
        return disp

    def load_image(index):
        nonlocal original_image, display_image, current_clicks, zoom_scale, zoom_center
        path = image_paths[index]
        original_image = cv2.imread(path)
        if original_image is None:
            print("Could not load image:", path)
            return
        current_clicks = []
        zoom_scale = 1.0
        zoom_center = None
        display_image = get_display_image()
        cv2.imshow("Image", display_image)

    def mouse_callback(event, x, y, flags, param):
        nonlocal current_clicks, display_image
        if event == cv2.EVENT_LBUTTONDOWN and len(current_clicks) < 1:
            current_clicks.append((x, y))
            cv2.circle(display_image, (x, y), 5, (0, 255, 0), -1)
            cv2.imshow("Image", display_image)

    cv2.namedWindow("Image")
    cv2.setMouseCallback("Image", mouse_callback)
    load_image(current_image_index)

    print("""
    Instructions:
    Left-click      : Add a point (1 per set).
    c               : Clear current selection.
    s               : Save set (requires exactly 1 point).
    d / a           : Next / previous image.
    + / -           : Zoom in / out.
    ← / ↑ / → / ↓   : Pan Left / Up / Right / Down when zoomed.
    Esc             : Quit and save data.json.
    """)

    while True:
        cv2.imshow("Image", display_image)
        key = cv2.waitKey(0) & 0xFF

        if key == 27:  # Esc
            break

        elif key == ord('c'):
            current_clicks = []
            display_image = get_display_image()
            print("Cleared selection.")

        elif key == ord('s'):
            if len(current_clicks) == 1:
                h, w = original_image.shape[:2]
                win_w, win_h = int(w / zoom_scale), int(h / zoom_scale)
                x_off = max(0, zoom_center[0] - win_w // 2)
                y_off = max(0, zoom_center[1] - win_h // 2)
                dx, dy = current_clicks[0]
                orig_x = int(x_off + dx / w * win_w)
                orig_y = int(y_off + dy / h * win_h)

                b, g, r = original_image[orig_y, orig_x]
                flake_color = [int(r), int(g), int(b)]
                rgb_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)
                red_mode = int(np.bincount(rgb_image[:, :, 0].flatten()).argmax())
                green_mode = int(np.bincount(rgb_image[:, :, 1].flatten()).argmax())
                blue_mode = int(np.bincount(rgb_image[:, :, 2].flatten()).argmax())
                background_color = [red_mode, green_mode, blue_mode]

                rgb_set = [background_color, flake_color]
                fname = os.path.basename(image_paths[current_image_index])
                saved_data.setdefault(fname, []).append(rgb_set)
                print(f"Saved for {fname}: BG {background_color}, Flake {flake_color}")
                current_clicks = []
                display_image = get_display_image()
            else:
                print("Select exactly one point before saving.")

        elif key == ord('d'):
            if current_image_index < len(image_paths) - 1:
                current_image_index += 1
                load_image(current_image_index)
            else:
                print("Last image.")

        elif key == ord('a'):
            if current_image_index > 0:
                current_image_index -= 1
                load_image(current_image_index)
            else:
                print("First image.")

        elif key == ord('+'):
            zoom_scale = min(zoom_scale * ZOOM_STEP, 10.0)
            display_image = get_display_image()
            print(f"Zoom: {zoom_scale:.2f}×")

        elif key == ord('-'):
            zoom_scale = max(zoom_scale / ZOOM_STEP, 1.0)
            display_image = get_display_image()
            print(f"Zoom: {zoom_scale:.2f}×")

        # Pan with arrow keys (key codes 81=←, 82=↑, 83=→, 84=↓)
        elif key in (81, 82, 83, 84):
            if zoom_scale > 1.0:
                dx = PAN_STEP / zoom_scale
                cx, cy = zoom_center
                if key == 82:   cy -= dx  # Up
                elif key == 84: cy += dx  # Down
                elif key == 81: cx -= dx  # Left
                elif key == 83: cx += dx  # Right
                h, w = original_image.shape[:2]
                zoom_center = (int(np.clip(cx, 0, w)), int(np.clip(cy, 0, h)))
                display_image = get_display_image()
                print(f"Panned to {zoom_center}.")

    cv2.destroyAllWindows()

    # Save data.json next to script
    script_directory = os.getcwd()
    save_dir = os.path.join(script_directory, "datapoints")
    os.makedirs(save_dir, exist_ok=True)
    data_path = os.path.join(save_dir, "true_data_points.json")
    with open(data_path, "w") as f:
        json.dump(saved_data, f, indent=4)
    print(f"\nData saved to {data_path}")


def invalid_area_data(folder=None):
    """Collect invalid area data - simplified to match valid_flake_data workflow"""
    import json
    import cv2
    import os
    import glob
    import numpy as np

    # Ask for the folder containing images
    if not folder:
        folder = input("Enter the path to the folder containing images: ").strip()

    # Gather image paths
    image_extensions = ["*.jpg", "*.jpeg", "*.png", "*.bmp", "*.tiff"]
    image_paths = []
    for ext in image_extensions:
        image_paths.extend(glob.glob(os.path.join(folder, ext)))
    image_paths.sort()
    if not image_paths:
        print("No images found in the provided folder.")
        return

    saved_data = {}
    current_image_index = 0
    current_clicks = []
    original_image = None
    display_image = None

    # Zoom / pan state
    zoom_scale = 1.0
    zoom_center = None
    ZOOM_STEP = 1.25
    PAN_STEP = 50

    def draw_overlay(img, filename):
        overlay = img.copy()
        cv2.putText(overlay, filename, (10, overlay.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        if filename in saved_data and saved_data[filename]:
            text = f"Saved sets: {len(saved_data[filename])}"
            cv2.putText(overlay, text, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        return overlay

    def get_display_image():
        nonlocal zoom_center
        h, w = original_image.shape[:2]
        if zoom_center is None:
            zoom_center = (w // 2, h // 2)

        win_w, win_h = int(w / zoom_scale), int(h / zoom_scale)
        cx, cy = zoom_center
        x1 = max(0, cx - win_w // 2)
        y1 = max(0, cy - win_h // 2)
        x2 = min(w, x1 + win_w)
        y2 = min(h, y1 + win_h)

        cropped = original_image[y1:y2, x1:x2]
        resized = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)
        disp = draw_overlay(resized, os.path.basename(image_paths[current_image_index]))
        for (x, y) in current_clicks:
            cv2.circle(disp, (x, y), 5, (0, 255, 0), -1)
        return disp

    def load_image(index):
        nonlocal original_image, display_image, current_clicks, zoom_scale, zoom_center
        path = image_paths[index]
        original_image = cv2.imread(path)
        if original_image is None:
            print("Could not load image:", path)
            return
        current_clicks = []
        zoom_scale = 1.0
        zoom_center = None
        display_image = get_display_image()
        cv2.imshow("Image", display_image)

    def mouse_callback(event, x, y, flags, param):
        nonlocal current_clicks, display_image
        if event == cv2.EVENT_LBUTTONDOWN and len(current_clicks) < 1:
            current_clicks.append((x, y))
            cv2.circle(display_image, (x, y), 5, (0, 255, 0), -1)
            cv2.imshow("Image", display_image)

    cv2.namedWindow("Image")
    cv2.setMouseCallback("Image", mouse_callback)
    load_image(current_image_index)

    print("""
    Instructions:
    Left-click      : Add a point (1 per set).
    c               : Clear current selection.
    s               : Save set (requires exactly 1 point).
    d / a           : Next / previous image.
    + / -           : Zoom in / out.
    ← / ↑ / → / ↓   : Pan Left / Up / Right / Down when zoomed.
    Esc             : Quit and save data.json.
    """)

    while True:
        cv2.imshow("Image", display_image)
        key = cv2.waitKey(0) & 0xFF

        if key == 27:  # Esc
            break

        elif key == ord('c'):
            current_clicks = []
            display_image = get_display_image()
            print("Cleared selection.")

        elif key == ord('s'):
            if len(current_clicks) == 1:
                h, w = original_image.shape[:2]
                win_w, win_h = int(w / zoom_scale), int(h / zoom_scale)
                x_off = max(0, zoom_center[0] - win_w // 2)
                y_off = max(0, zoom_center[1] - win_h // 2)
                dx, dy = current_clicks[0]
                orig_x = int(x_off + dx / w * win_w)
                orig_y = int(y_off + dy / h * win_h)

                b, g, r = original_image[orig_y, orig_x]
                invalid_color = [int(r), int(g), int(b)]
                rgb_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)
                red_mode = int(np.bincount(rgb_image[:, :, 0].flatten()).argmax())
                green_mode = int(np.bincount(rgb_image[:, :, 1].flatten()).argmax())
                blue_mode = int(np.bincount(rgb_image[:, :, 2].flatten()).argmax())
                background_color = [red_mode, green_mode, blue_mode]

                rgb_set = [background_color, invalid_color]
                fname = os.path.basename(image_paths[current_image_index])
                saved_data.setdefault(fname, []).append(rgb_set)
                print(f"Saved for {fname}: BG {background_color}, Invalid {invalid_color}")
                current_clicks = []
                display_image = get_display_image()
            else:
                print("Select exactly one point before saving.")

        elif key == ord('d'):
            if current_image_index < len(image_paths) - 1:
                current_image_index += 1
                load_image(current_image_index)
            else:
                print("Last image.")

        elif key == ord('a'):
            if current_image_index > 0:
                current_image_index -= 1
                load_image(current_image_index)
            else:
                print("First image.")

        elif key == ord('+'):
            zoom_scale = min(zoom_scale * ZOOM_STEP, 10.0)
            display_image = get_display_image()
            print(f"Zoom: {zoom_scale:.2f}×")

        elif key == ord('-'):
            zoom_scale = max(zoom_scale / ZOOM_STEP, 1.0)
            display_image = get_display_image()
            print(f"Zoom: {zoom_scale:.2f}×")

        # Pan with arrow keys (key codes 81=←, 82=↑, 83=→, 84=↓)
        elif key in (81, 82, 83, 84):
            if zoom_scale > 1.0:
                dx = PAN_STEP / zoom_scale
                cx, cy = zoom_center
                if key == 82:   cy -= dx  # Up
                elif key == 84: cy += dx  # Down
                elif key == 81: cx -= dx  # Left
                elif key == 83: cx += dx  # Right
                h, w = original_image.shape[:2]
                zoom_center = (int(np.clip(cx, 0, w)), int(np.clip(cy, 0, h)))
                display_image = get_display_image()
                print(f"Panned to {zoom_center}.")

    cv2.destroyAllWindows()

    # Save data.json next to script
    script_directory = os.getcwd()
    save_dir = os.path.join(script_directory, "datapoints")
    os.makedirs(save_dir, exist_ok=True)
    data_path = os.path.join(save_dir, "false_data_points.json")
    with open(data_path, "w") as f:
        json.dump(saved_data, f, indent=4)
    print(f"\nData saved to {data_path}")


def add_label_to_data(json_path, label, output_path="data_labeled.json"):
    """
    Loads the JSON file created by the image annotation code, 
    appends the specified label to each saved set, and writes
    the result to a new JSON file.
    
    Parameters:
        json_path (str): Path to the existing JSON file.
        label (int): The label to add (e.g., 1 for few layers, 0 for not).
        output_path (str): Path for the output labeled JSON file.
    """
    # Load existing data
    with open(json_path, "r") as f:
        data = json.load(f)
    
    # Loop over each image and each set, appending the label.
    for img_file in data:
        updated_sets = []
        for flake_set in data[img_file]:
            # Check if this set already has a label (avoid duplicate labeling)
            if len(flake_set) == 2:
                # Append the label, making the set [background, flake, label]
                updated_sets.append(flake_set + [label])
            else:
                # If already labeled, you might decide to update or skip
                updated_sets.append(flake_set)
        data[img_file] = updated_sets
    
    # Write the updated data to a new JSON file.
    with open(output_path, "w") as f:
        json.dump(data, f, indent=4)
    
    print(f"Labeled data has been saved to {output_path}")


def load_json(file_path):
    """Helper function to load JSON file"""
    with open(file_path, 'r') as f:
        return json.load(f)


def combine_and_shuffle(file1, file2, output_file):
    """
    Combine two labeled datasets, shuffle them, and save to output file.
    
    Parameters:
        file1 (str): Path to first labeled JSON file (e.g., labeled true data)
        file2 (str): Path to second labeled JSON file (e.g., labeled false data)
        output_file (str): Path for the combined and shuffled output file
    """
    # Load both labeled datasets.
    data_true = load_json(file1)
    data_false = load_json(file2)

    combined = []

    # Process first file (e.g., labeled true) and add each data entry with its filename.
    for filename, items in data_true.items():
        for item in items:
            combined.append({
                "filename": filename,
                "data": item
            })

    # Process second file (e.g., labeled false) similarly.
    for filename, items in data_false.items():
        for item in items:
            combined.append({
                "filename": filename,
                "data": item
            })

    # Shuffle the combined list randomly.
    random.shuffle(combined)

    # Write the combined and shuffled data to the output file.
    with open(output_file, 'w') as f:
        json.dump(combined, f, indent=4)

    print(f"Combined and shuffled {len(combined)} items saved to {output_file}")