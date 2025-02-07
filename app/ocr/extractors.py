# app/ocr/extractors.py
import re
from typing import Optional

class TextExtractor:
    def __init__(self):
        self.dosage_forms = ['tablet', 'capsule', 'syrup', 'injection', 'cream', 'ointment']
        self.countries = ['USA', 'UK', 'India', 'Germany', 'Switzerland', 'France']

    def extract_brand_name(self, text: str) -> Optional[str]:
        match = re.search(r'([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)[®™]', text)
        return match.group(1) if match else None

    def extract_generic_name(self, text: str) -> Optional[str]:
        match = re.search(r'\(([\w\s-]+)\)', text)
        return match.group(1) if match else None

    def extract_dosage_form(self, text: str) -> Optional[str]:
        text_lower = text.lower()
        for form in self.dosage_forms:
            if form in text_lower:
                return form
        return None

    def extract_manufacturer_country(self, text: str) -> Optional[str]:
        text_upper = text.upper()
        for country in self.countries:
            if f"MADE IN {country}" in text_upper or f"MANUFACTURED IN {country}" in text_upper:
                return country
        return None

    def extract_strength(self, text: str) -> Optional[str]:
        match = re.search(r'(\d+(?:\.\d+)?\s*(?:mg|ml|g|mcg)/?(?:\d+(?:\.\d+)?\s*(?:mg|ml|g|mcg))?)', text)
        return match.group(1) if match else None

    def extract_description(self, text: str) -> Optional[str]:
        match = re.search(r'description:?\s*([^.]+)', text, re.IGNORECASE)
        return match.group(1) if match else None

    def extract_precaution(self, text: str) -> Optional[str]:
        match = re.search(r'(?:precaution|warning):?\s*([^.]+)', text, re.IGNORECASE)
        return match.group(1) if match else None