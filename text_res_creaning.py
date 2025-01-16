import re
import json
import unicodedata
import pandas as pd
import logging
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from tqdm import tqdm

# Configure logging
def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration with enhanced debugging"""
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatter with additional debug info
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.handlers = [console_handler]
    
    # Add file handler for debug logs
    if log_level == logging.DEBUG:
        file_handler = logging.FileHandler("text_cleaning_debug.log", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

logger = logging.getLogger(__name__)
setup_logging()

def log_operation_start(operation: str) -> None:
    """Log the start of an operation with debug info"""
    logger.debug(f"Starting operation: {operation}")
    logger.debug(f"Face marks loaded: {len(FACE_MARKS)} patterns")

def log_operation_end(operation: str, success: bool = True) -> None:
    """Log the end of an operation with status"""
    status = "completed successfully" if success else "failed"
    logger.debug(f"Operation {operation} {status}")

# Load face marks from external config
def load_face_marks(config_path: Optional[str] = None) -> Dict[str, str]:
    """Load face mark patterns from config file or use defaults"""
    default_marks = {
        r"\(ﾟ∀ﾟ\)": "[FACE_TOKEN_1]",
        r"\(゚∀゚\)": "[FACE_TOKEN_1]",  # Variant
        r"ｷﾀ━━━━\(ﾟ∀ﾟ\)━━━━": "[FACE_TOKEN_2]",
    }
    
    if config_path and Path(config_path).exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load face marks config: {e}. Using defaults.")
    
    return default_marks

FACE_MARKS = load_face_marks()

def tokenize_face_marks(text: str) -> str:
    """
    Replace face marks with tokens
    
    Args:
        text (str): Input text containing face marks
        
    Returns:
        str: Text with face marks replaced by tokens
        
    Raises:
        ValueError: If text is empty or None
    """
    if not text:
        raise ValueError("Input text cannot be empty")
        
    try:
        # Process face marks in order of longest to shortest patterns
        for pattern, token in sorted(FACE_MARKS.items(), 
                                   key=lambda x: len(x[0]), 
                                   reverse=True):
            text = re.sub(pattern, token, text)
        return text
    except Exception as e:
        logger.error(f"Error tokenizing face marks: {e}")
        raise

def restore_face_marks(text: str) -> str:
    """Restore face marks from tokens"""
    token_to_face = {v: k for k, v in FACE_MARKS.items()}
    for token, face in token_to_face.items():
        text = text.replace(token, face)
    return text

def clean_text(text: str) -> str:
    """Main text cleaning function"""
    if not isinstance(text, str):
        return ""
        
    try:
        # 1. Normalize characters first
        text = unicodedata.normalize("NFKC", text)
        
        # 2. Remove HTML tags and their content
        text = re.sub(r"<[^>]+>(.*?)<\/[^>]+>", "", text)
        text = re.sub(r"<[^>]+>", "", text)  # Remove any remaining tags
        
        # 3. Remove URLs and usernames
        text = re.sub(r"https?://\S+|www\.\S+", "", text)
        text = re.sub(r"@[\w\d_]+", "", text)
        
        # 4. Remove anchors and special characters
        text = re.sub(r">>\d{1,4}", "", text)
        text = re.sub(r"[^\w\s\u3000\u3040-\u30FF\u4E00-\u9FFF\[\]\(\)]", "", text)
        
        # 5. Tokenize face marks (preserve brackets)
        text = tokenize_face_marks(text)
        
        # 6. Clean whitespace and special spaces
        text = text.strip()
        # Normalize all whitespace characters
        text = re.sub(r"[\u200b\u200c\u200d\u2060\ufeff]", "", text)  # Remove zero-width spaces
        text = re.sub(r"[\u3000\u00a0]", " ", text)  # Convert full-width and non-breaking spaces to normal spaces
        text = re.sub(r"\s+", " ", text)  # Collapse multiple spaces
        text = text.replace("\\", "")
        
        # Log detailed processing info
        logger.debug(f"Processed text: {text[:50]}...")
        
        return text.strip()
    except Exception as e:
        logger.error(f"Error cleaning text: {e}")
        return ""

def clean_csv(input_path: str, output_path: str) -> bool:
    """
    Process CSV file containing text data
    
    Args:
        input_path (str): Path to input CSV file
        output_path (str): Path to save cleaned CSV
        
    Returns:
        bool: True if operation succeeded, False otherwise
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        pd.errors.EmptyDataError: If CSV is empty
        pd.errors.ParserError: If CSV parsing fails
        ValueError: If required columns are missing
    """
    try:
        log_operation_start("CSV cleaning")
        
        # Validate input path
        if not Path(input_path).exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
            
        logger.info(f"Processing CSV file: {input_path}")
        logger.debug(f"Output path: {output_path}")
        
        # Try multiple encodings for CSV reading
        encodings = ["utf-8-sig", "shift_jis", "cp932", "euc-jp"]
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(
                    input_path,
                    encoding=encoding,
                    header=0,
                    dtype=str,
                    na_values=["", " ", "　"],
                    keep_default_na=False
                )
                break
            except UnicodeDecodeError:
                continue
                
        if df is None:
            raise ValueError(f"Failed to read CSV with supported encodings: {encodings}")
            
        # Clean column names and strip whitespace
        df.columns = df.columns.str.strip()
        
        # Check if required columns exist
        required_columns = ["レス番号", "内容"]
        
        # Convert all columns to string type and strip whitespace
        df = df.astype(str)
        df = df.apply(lambda x: x.str.strip())
        
        # Remove duplicate header rows if any
        df = df[~df.iloc[:, 0].str.contains("レス番号|^Unnamed:", na=False, regex=True)]
        
        # Validate data content
        if df.empty:
            raise ValueError("CSVファイルに有効なデータが見つかりませんでした。ファイル形式を確認してください。")
        
        # Validate columns - check if at least required columns exist
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

        # Select only required columns
        df = df[required_columns].dropna().reset_index(drop=True)
        
        # Remove any potential duplicate rows
        df = df.drop_duplicates()

        # Clean texts with progress logging and timing
        logger.info("Cleaning text data...")
        start_time = time.time()
        
        # Add progress bar
        tqdm.pandas(desc="Cleaning progress")
        df["内容"] = df["内容"].progress_apply(clean_text)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Cleaning completed in {elapsed_time:.2f} seconds")

        # Save cleaned CSV
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        logger.info(f"Successfully saved cleaned data to: {output_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error processing CSV: {e}")
        return False

def main() -> None:
    """Main entry point for text cleaning tool"""
    import argparse
    
    log_operation_start("Text cleaning tool initialization")
    
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Text cleaning tool for processing forum data",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "input",
        help="Input CSV file path"
    )
    parser.add_argument(
        "output",
        help="Output CSV file path"
    )
    parser.add_argument(
        "--face-config",
        help="Path to face marks configuration file",
        default=None
    )
    parser.add_argument(
        "--log-level",
        help="Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    )
    
    args = parser.parse_args()
    setup_logging(args.log_level)
    
    logger.debug(f"Input path: {args.input}")
    logger.debug(f"Output path: {args.output}")
    logger.debug(f"Face config path: {args.face_config}")
    
    # Load face marks configuration if provided
    global FACE_MARKS
    if args.face_config:
        FACE_MARKS = load_face_marks(args.face_config)
    
    # Process CSV with error handling
    success = clean_csv(args.input, args.output)
    
    if not success:
        logger.error("Failed to process CSV file")
        exit(1)

if __name__ == "__main__":
    main()
