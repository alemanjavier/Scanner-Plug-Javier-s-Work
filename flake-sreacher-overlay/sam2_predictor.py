"""
SAM2 Predictor Wrapper
A wrapper around SAM2 for easy point-based segmentation
"""
import numpy as np
import cv2
import os

try:
    import torch
    from sam2.build_sam import build_sam2
    from sam2.sam2_image_predictor import SAM2ImagePredictor
    SAM2_AVAILABLE = True
except ImportError as e:
    SAM2_AVAILABLE = False
    print(f"Warning: SAM2 not fully available: {e}")


class FastSAMPredictor:
    """Wrapper for SAM2 that provides a simple interface for point-based segmentation"""
    
    def __init__(self, model_cfg="sam2_hiera_s", checkpoint=None, device='cpu'):
        """
        Initialize SAM2 predictor
        
        Parameters:
        -----------
        model_cfg : str
            Model configuration name (e.g., "sam2.1/sam2.1_hiera_s")
        checkpoint : str, optional
            Path to checkpoint file. If None, will try to download or use default
        device : str
            Device to run on ('cpu' or 'cuda')
        """
        self.device = device
        self.predictor = None
        self.model_cfg = model_cfg
        self.checkpoint = checkpoint
        self.current_image = None
        
        if not SAM2_AVAILABLE:
            raise ImportError("SAM2 is not available. Please install it with: pip install git+https://github.com/facebookresearch/segment-anything-2.git")
        
        # Try to initialize SAM2
        try:
            # Build SAM2 model
            sam2_model = build_sam2(model_cfg, checkpoint=checkpoint, device=device)
            self.predictor = SAM2ImagePredictor(sam2_model)
            print(f"SAM2 initialized successfully on {device}")
        except Exception as e:
            print(f"Warning: Could not initialize SAM2: {e}")
            print("You may need to download the model checkpoint file.")
            raise RuntimeError(f"Failed to initialize SAM2: {e}")
    
    def set_image(self, image):
        """
        Set the image for prediction
        
        Parameters:
        -----------
        image : np.ndarray
            Input image in BGR format (as from cv2.imread)
        """
        if self.predictor is None:
            raise RuntimeError("SAM2 predictor not initialized")
        
        # Store original image for overlay creation
        self.current_image = image.copy()
        
        # Convert BGR to RGB for SAM2
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        self.predictor.set_image(image_rgb)
    
    def segment_points(self, points, labels=None):
        """
        Segment image based on point prompts
        
        Parameters:
        -----------
        points : list of tuples
            List of (x, y) coordinates
        labels : list of int, optional
            Labels for each point (1 for foreground, 0 for background)
            If None, all points are treated as foreground
        
        Returns:
        --------
        overlay : np.ndarray
            Overlay image with mask visualization (BGR format)
        mask : np.ndarray
            Boolean mask of the segmented region
        """
        if self.predictor is None:
            raise RuntimeError("SAM2 predictor not initialized")
        
        if not points:
            raise ValueError("No points provided")
        
        if self.current_image is None:
            raise RuntimeError("No image set. Call set_image() first.")
        
        # Convert points to numpy array
        points_array = np.array(points, dtype=np.float32)
        
        # Default labels: all points are foreground (1)
        if labels is None:
            labels_array = np.ones(len(points), dtype=np.int32)
        else:
            labels_array = np.array(labels, dtype=np.int32)
        
        # Get mask and scores
        masks, scores, _ = self.predictor.predict(
            point_coords=points_array,
            point_labels=labels_array,
            multimask_output=False
        )
        
        # Get the best mask
        mask = masks[0]  # Boolean mask
        
        # Create overlay visualization
        overlay = self._create_overlay(mask)
        
        return overlay, mask
    
    def _create_overlay(self, mask):
        """
        Create a colored overlay from a mask
        
        Parameters:
        -----------
        mask : np.ndarray
            Boolean mask
            
        Returns:
        --------
        overlay : np.ndarray
            Colored overlay image in BGR format
        """
        # Create overlay by blending original image with colored mask
        overlay = self.current_image.copy()
        
        # Create colored mask (semi-transparent green)
        colored_mask = np.zeros_like(overlay)
        colored_mask[mask] = [0, 255, 0]  # Green in BGR
        
        # Blend with original image (50% opacity)
        overlay = cv2.addWeighted(overlay, 0.5, colored_mask, 0.5, 0)
        
        return overlay
