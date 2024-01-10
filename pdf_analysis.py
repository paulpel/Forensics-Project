import argparse
import os
import sys
from datetime import datetime
import pytz
import fitz
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import tempfile
from pdf2image import convert_from_path
from PIL import Image, ImageDraw
from PyPDF2 import PdfWriter
from datetime import datetime
import pytz


def find_pdfs(root_dir):
    """
    Recursively searches for and lists all PDF files in a given directory.

    :param root_dir: The root directory to start the search from.
    :type root_dir: str
    :return: A list of paths to all the PDF files found.
    :rtype: list of str

    This function traverses through the given directory and its subdirectories, looking
    for files with a '.pdf' extension. It returns a list of full file paths to these PDF files.
    """
    pdf_files = []
    for root, dirs, _ in os.walk(root_dir):
        for dir in dirs:
            if dir.lower() == "pdf":
                dir_path = os.path.join(root, dir)
                for root2, _, files2 in os.walk(dir_path):
                    for file in files2:
                        if file.lower().endswith(".pdf"):
                            full_file_path = os.path.join(root2, file)
                            pdf_files.append(full_file_path)
    return pdf_files


def extract_text_from_pdf(pdf_path):
    """
    Extracts and returns the text content from a single PDF file.

    :param pdf_path: Path to the PDF file.
    :type pdf_path: str
    :return: Extracted text from the PDF.
    :rtype: str

    This function opens a PDF file at the given path and extracts all the textual content
    from each page. It concatenates and returns this content as a single string.
    """
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text


def search_words_in_text(text, words_to_search):
    """
    Counts the occurrences of specific words in a given text.

    :param text: The text to search within.
    :type text: str
    :param words_to_search: A list of words to count in the text.
    :type words_to_search: list of str
    :return: A dictionary with each word and its count in the text.
    :rtype: dict

    This function takes a string of text and a list of words, then counts how many times
    each word appears in the text. It returns a dictionary where keys are the words and
    values are their corresponding counts.
    """
    word_count = {word: text.lower().count(word.lower()) for word in words_to_search}
    return word_count


def write_analysis_to_file(results, output_file):
    """
    Writes the results of a PDF analysis to a PDF file.

    :param results: The analysis results to write.
    :type results: dict
    :param output_file: The path where the results PDF should be saved.
    :type output_file: str
    :returns: None

    This function takes the analysis results, which are in the form of a dictionary mapping
    PDF file paths to word counts, and writes this information into a new PDF file. The file
    is saved at the specified output path.
    """

    pdfmetrics.registerFont(TTFont("DejaVuSans", "DejaVuSans.ttf"))

    c = canvas.Canvas(output_file, pagesize=letter)
    width, height = letter
    y_position = height - 40
    x_position = 40

    c.setFont("DejaVuSans", 12)
    c.drawString(x_position, y_position, "PDF Analysis Results")
    c.setFont("DejaVuSans", 10)
    y_position -= 20

    for pdf, counts in results.items():
        for word, count in counts.items():
            if count == 0:
                break
            else:
                y_position -= 15
                c.drawString(
                    x_position, y_position, f"{word} found in {pdf}, count:{count}"
                )
                y_position -= 10

                # y_position -= 12
                # c.drawString(x_position + 20, y_position, f"{word}: {count}")
                if y_position < 40:
                    c.showPage()
                    y_position = height - 40

            y_position -= 10
            if y_position < 40:
                c.showPage()
                y_position = height - 40

    c.save()


def encode_pdf(input_pdf, password):
    """
    Encrypts a PDF file and adds a timestamp watermark to each page.

    :param input_pdf: Path to the PDF file to be encrypted and watermarked.
    :type input_pdf: str
    :param password: Password to be used for encrypting the PDF.
    :type password: str
    :returns: None

    This function first converts each page of the given PDF into an image, then adds a
    watermark with the current date and time. These watermarked images are then assembled
    back into a PDF, which is encrypted with the given password.
    """
    images = convert_from_path(input_pdf)

    # Create a new PDF writer
    pdf_writer = PdfWriter()

    # Get current date and time
    timezone = pytz.timezone("Europe/Warsaw")
    current_datetime = datetime.now(timezone).strftime(
        "Date: %Y-%m-%d \nTime: %H:%M:%S"
    )

    for image in images:
        # Draw watermark
        draw = ImageDraw.Draw(image)
        text = f"Timestamp: {current_datetime}"
        draw.text(
            (10, 10), text=text, fill=(185, 185, 185)
        )  # Adjust position and color as needed

        # Save image to a temporary file
        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        image.save(temp_pdf, format="PDF")
        pdf_writer.append(temp_pdf.name)

    # Apply password protection
    pdf_writer.encrypt(password)

    with open(input_pdf, "wb") as output_file:
        pdf_writer.write(output_file)


def pdf_analysis(dir_to_analyze, words_to_search, password):
    """
    Conducts a PDF analysis in a directory, searching for specific words.

    :param dir_to_analyze: The directory containing PDF files to analyze.
    :type dir_to_analyze: str
    :param words_to_search: Words to search for in the PDF files.
    :type words_to_search: list of str
    :param password: Password for encrypting the analysis results PDF.
    :type password: str
    :return: Analysis results mapping each PDF file to its word counts.
    :rtype: dict

    This function searches for PDF files in the specified directory, extracts text from
    them, and then searches for specified words. The word counts in each PDF are compiled
    into results, which are then written to a new encrypted PDF file.
    """
    timezone = pytz.timezone("Europe/Warsaw")
    current_datetime = datetime.now(timezone).strftime("%Y_%m_%d_%H_%M_%S")

    pdf_files = find_pdfs(dir_to_analyze)
    results = {}

    for pdf in pdf_files:
        text = extract_text_from_pdf(pdf)
        results[pdf] = search_words_in_text(text, words_to_search)

    output_file = f"pdf_analysis_{current_datetime}.pdf"
    write_analysis_to_file(results, output_file)
    encode_pdf(output_file, password)

    print(f"Analysis results written to {output_file}")
    return results


def main(dir_to_analyze, words_to_search, password):
    """
    Main function to initiate PDF analysis in a specified directory.

    :param dir_to_analyze: The directory to search for and analyze PDF files.
    :type dir_to_analyze: str
    :param words_to_search: A list of words to search for in the PDF files.
    :type words_to_search: list of str
    :param password: Password for encrypting the output PDF file.
    :type password: str
    :returns: None

    This function serves as the main entry point for the PDF analysis process. It
    calls `pdf_analysis` with the specified directory, words to search, and password,
    then prints out the analysis results for each PDF file.
    """
    analysis_results = pdf_analysis(dir_to_analyze, words_to_search, password)
    for pdf, counts in analysis_results.items():
        print(f"Analysis for {pdf}:")
        for word, count in counts.items():
            print(f"  {word}: {count}")
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Utility to analyze pdf files")
    parser.add_argument("DIR_ANALYSIS", help="Evidence file path")
    parser.add_argument("WORDS", nargs="+", help="Words to search in PDF files")
    parser.add_argument("PASSWORD", nargs="+", help="Password to protect analysis file")

    args = parser.parse_args()

    if os.path.exists(args.DIR_ANALYSIS) and os.path.isdir(args.DIR_ANALYSIS):
        main(args.DIR_ANALYSIS, args.WORDS, args.PASSWORD)
    else:
        print(f"[-] Supplied input directory {args.DIR_ANALYSIS} does not exist")
        sys.exit(1)
