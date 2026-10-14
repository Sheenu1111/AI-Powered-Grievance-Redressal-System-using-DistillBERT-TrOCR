import cv2
import numpy as np
from PIL import Image
import os

class ImageProcessor:
    """Preprocess images for better OCR accuracy using OpenCV"""
    
    @staticmethod
    def preprocess_image(image_path, output_path=None):
        """
        Preprocess image for OCR
        
        Args:
            image_path: Path to input image
            output_path: Path to save preprocessed image (optional)
            
        Returns:
            Path to preprocessed image
        """
        try:
            # Read image
            img = cv2.imread(image_path)
            
            if img is None:
                raise ValueError(f"Could not read image: {image_path}")
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply denoising
            denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
            
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Deskew the image
            coords = np.column_stack(np.where(thresh > 0))
            angle = cv2.minAreaRect(coords)[-1]
            
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            
            # Only rotate if angle is significant
            if abs(angle) > 0.5:
                (h, w) = thresh.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                rotated = cv2.warpAffine(
                    thresh, M, (w, h),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE
                )
            else:
                rotated = thresh
            
            # Enhance contrast
            enhanced = cv2.equalizeHist(rotated)
            
            # Save preprocessed image
            if output_path is None:
                base_name = os.path.basename(image_path)
                name, ext = os.path.splitext(base_name)
                output_path = os.path.join(
                    os.path.dirname(image_path),
                    f"{name}_preprocessed{ext}"
                )
            
            cv2.imwrite(output_path, enhanced)
            
            return output_path
        
        except Exception as e:
            print(f"Error in image preprocessing: {str(e)}")
            # Return original image path if preprocessing fails
            return image_path
    
    @staticmethod
    def validate_image(image_path):
        """
        Validate if file is a valid image
        
        Args:
            image_path: Path to image file
            
        Returns:
            Boolean indicating validity
        """
        try:
            img = Image.open(image_path)
            img.verify()
            return True
        except Exception:
            return False
