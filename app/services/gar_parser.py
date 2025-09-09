# app/services/gar_parser.py

def parse_compliance_doc(file_path):
    """
    Simulated AI parser. Replace with real model or OCR/NLP.
    """
    # For now, return dummy values
    return (
        f"Extracted content from {os.path.basename(file_path)}",
        {
            "summary": "Auto-parsed summary placeholder",
            "extracted_fields": {
                "insurer": "Sample Insurer",
                "coverage": "€2,000,000"
            }
        }
    )
