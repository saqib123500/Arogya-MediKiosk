from paddleocr import PaddleOCR


class MedicalDocumentOCR:

    def __init__(self):
        self.ocr = PaddleOCR(
            lang="en"
        )

    def extract_text(self, image_path):

        result = self.ocr.predict(image_path)

        extracted_text = []

        for page in result:

            if hasattr(page, "json"):

                data = page.json

                if isinstance(data, str):
                    import json
                    data = json.loads(data)

                result_data = data.get("res", {})

                texts = result_data.get(
                    "rec_texts",
                    []
                )

                extracted_text.extend(texts)

        return "\n".join(extracted_text)
    
    