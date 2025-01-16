import re
import unicodedata
import pandas as pd
from typing import Dict, List

# Face mark patterns and their token mappings
FACE_MARKS = {
    r"\(ﾟ∀ﾟ\)": "[FACE_TOKEN_1]",
    r"\(゚∀゚\)": "[FACE_TOKEN_1]",  # Variant
    r"ｷﾀ━━━━\(ﾟ∀ﾟ\)━━━━": "[FACE_TOKEN_2]",
    # Add more patterns as needed
}

def tokenize_face_marks(text: str) -> str:
    """Replace face marks with tokens"""
    for pattern, token in FACE_MARKS.items():
        text = re.sub(pattern, token, text)
    return text

def restore_face_marks(text: str) -> str:
    """Restore face marks from tokens"""
    token_to_face = {v: k for k, v in FACE_MARKS.items()}
    for token, face in token_to_face.items():
        text = text.replace(token, face)
    return text

def clean_text(text: str) -> str:
    """Main text cleaning function"""
    # 1. Tokenize face marks
    text = tokenize_face_marks(text)

    # 2. Remove unwanted elements
    text = re.sub(r"http\S+", "", text)  # URLs
    text = re.sub(r"@[A-Za-z0-9_]+", "", text)  # Usernames
    text = re.sub(r"<[^>]*>", "", text)  # HTML tags
    text = re.sub(r">>\d+", "", text)  # Anchors (optional)

    # 3. Normalize characters
    text = unicodedata.normalize("NFKC", text)

    # 4. Clean whitespace
    text = text.strip().replace("\n", " ")
    text = re.sub(r"\s+", " ", text)

    # 5. Restore face marks
    text = restore_face_marks(text)

    return text

def clean_csv(input_path: str, output_path: str) -> None:
    """Process CSV file"""
    try:
        # Read CSV and select necessary columns
        df = pd.read_csv(input_path, encoding="utf-8")
        
        # Check if required columns exist
        required_columns = ["レス番号", "内容"]
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"CSV must contain '{col}' column")

        # Select only necessary columns
        df = df[required_columns]

        # Clean texts
        df["内容"] = df["内容"].apply(clean_text)

        # Save cleaned CSV
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        
    except Exception as e:
        print(f"Error processing CSV: {str(e)}")
        raise

def main():
    import argparse
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Text cleaning tool")
    parser.add_argument("input", help="Input CSV file path")
    parser.add_argument("output", help="Output CSV file path")
    
    args = parser.parse_args()
    
    # Process CSV
    clean_csv(args.input, args.output)
    print(f"Cleaned text saved to {args.output}")

if __name__ == "__main__":
    main()
