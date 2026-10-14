from PIL import Image
import torch
from config import TROCR_MODEL

class OCRModel:
    """TrOCR model for handwriting recognition."""

    def __init__(self):
        self.processor = None
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def _ensure_loaded(self):
        """Load TrOCR only when OCR is actually needed."""
        if self.model is not None and self.processor is not None:
            return True

        try:
            from transformers import TrOCRProcessor, VisionEncoderDecoderModel

            print("Loading TrOCR model... This may take a few minutes on first run.")
            self.processor = TrOCRProcessor.from_pretrained(TROCR_MODEL)
            self.model = VisionEncoderDecoderModel.from_pretrained(TROCR_MODEL)
            self.model.to(self.device)
            print(f"TrOCR model loaded successfully on {self.device}!")
            return True
        except Exception as e:
            print(f"TrOCR model could not be loaded ({e}). OCR will be unavailable.")
            self.processor = None
            self.model = None
            return False

    def extract_text(self, image_path):
        """Extract text from an image using TrOCR."""
        if not self._ensure_loaded():
            return None

        try:
            image = Image.open(image_path).convert("RGB")
            pixel_values = self.processor(image, return_tensors="pt").pixel_values
            pixel_values = pixel_values.to(self.device)

            generated_ids = self.model.generate(pixel_values)
            generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            return generated_text.strip()

        except Exception as e:
            print(f"Error in OCR extraction: {str(e)}")
            return None

# Global instance (loaded once at startup)
ocr_model = None

def get_ocr_model():
    """Get or create OCR model instance"""
    global ocr_model
    if ocr_model is None:
        ocr_model = OCRModel()
    return ocr_model
