# app/ocr/processor.py
import re
import easyocr
import pytesseract
import cv2
import numpy as np
from datetime import datetime
from ..models import ProductData
from ..config import settings
from .extractors import TextExtractor

class OCRProcessor:
    def __init__(self):
        self.reader = easyocr.Reader(['en'])
        self.extractor = TextExtractor()
        pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
        
        self.patterns = {
            'certificate_number': r'certificate.*?([A-Z0-9-]+)',
            'batch_number': r'batch.*?([A-Z0-9-]+)',
            'expiry_date': r'exp.*?(\d{2}[-/]\d{2}[-/]\d{4})',
            'pack_size': r'pack.*?(\d+)'
        }

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        # Resize if image is too large
        h, w = image.shape[:2]
        if max(h, w) > settings.MAX_IMAGE_SIZE:
            scale = settings.MAX_IMAGE_SIZE / max(h, w)
            image = cv2.resize(image, None, fx=scale, fy=scale)
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray)
        thresh = cv2.adaptiveThreshold(
            denoised, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        return thresh

    def extract_text(self, image: np.ndarray) -> str:
        processed = self.preprocess_image(image)
        
        # EasyOCR detection
        easyocr_results = self.reader.readtext(
            processed, 
            min_size=10,
            contrast_ths=0.1,
            adjust_contrast=0.5,
            width_ths=0.7
        )
        
        # Tesseract detection
        tesseract_text = pytesseract.image_to_string(
            processed,
            config='--psm 11 --oem 3'
        )
        
        # Combine results
        combined_text = ' '.join([
            result[1] for result in easyocr_results 
            if result[2] > settings.MIN_CONFIDENCE
        ])
        return f"{combined_text} {tesseract_text}"

    def extract_product_info(self, image: np.ndarray) -> ProductData:
        text = self.extract_text(image)
        data = {}
        
        # Extract pattern-based fields
        for field, pattern in self.patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            data[field] = match.group(1) if match else None

        # Convert expiry date if found
        if data.get('expiry_date'):
            try:
                data['expiry_date'] = datetime.strptime(
                    data['expiry_date'], 
                    '%d/%m/%Y'
                ).date()
            except ValueError:
                data['expiry_date'] = None

        # Extract fields using specialized extractors
        data.update({
            'brand_name': self.extractor.extract_brand_name(text),
            'generic_name': self.extractor.extract_generic_name(text),
            'dosage_form': self.extractor.extract_dosage_form(text),
            'manufacturer_country': self.extractor.extract_manufacturer_country(text),
            'strength': self.extractor.extract_strength(text),
            'description': self.extractor.extract_description(text),
            'precaution': self.extractor.extract_precaution(text),
            'classification': None,
            'manufacturer': None,
            'self_administered': None,
            'display_name': None,
            'image_url': None
        })

        return ProductData(**data)