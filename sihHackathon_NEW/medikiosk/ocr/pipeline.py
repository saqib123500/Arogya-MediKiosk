import json

from medikiosk.ocr.processor import MedicalDocumentOCR
from medikiosk.ocr.extractor import MedicalTextExtractor


class MedicalDocumentPipeline:

    def __init__(self):

        self.ocr = MedicalDocumentOCR()
        self.extractor = MedicalTextExtractor()

    def process(self, image_path):

        # ================================================
        # STEP 1 — OCR
        # ================================================

        raw_text = self.ocr.extract_text(
            image_path
        )

        # ================================================
        # STEP 2 — STRUCTURED EXTRACTION
        # ================================================

        structured_data = self.extractor.extract(
            raw_text
        )

        # ================================================
        # FINAL RESULT
        # ================================================

        return {
            "raw_text": raw_text,
            "structured_data": structured_data
        }


# ========================================================
# TEST
# ========================================================

if __name__ == "__main__":

    IMAGE_PATH = "medikiosk/ocr/test_report.png"

    pipeline = MedicalDocumentPipeline()

    result = pipeline.process(
        IMAGE_PATH
    )

    print(
        "\n========== RAW OCR TEXT ==========\n"
    )

    print(
        result["raw_text"]
    )

    print(
        "\n========== STRUCTURED DATA ==========\n"
    )

    print(
        json.dumps(
            result["structured_data"],
            indent=4,
            ensure_ascii=False
        )
    )

    print(
        "\n======================================\n"
    )
    
