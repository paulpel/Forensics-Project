import argparse
import os
import sys
import pytsk3
import pyewf
import base64
from tabulate import tabulate
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from PyPDF2 import PdfReader, PdfWriter
from datetime import datetime


class EWFImgInfo(pytsk3.Img_Info):
    """
    Handles EWF (Expert Witness Format) image files using pytsk3 library.

    :param ewf_handle: A handle to an EWF file opened using pyewf.
    """

    def __init__(self, ewf_handle):
        self._ewf_handle = ewf_handle
        super(EWFImgInfo, self).__init__(url="", type=pytsk3.TSK_IMG_TYPE_EXTERNAL)

    def close(self):
        """Closes the EWF handle."""
        self._ewf_handle.close()

    def read(self, offset, size):
        """
        Reads data from the EWF image file.

        :param offset: The offset from which to start reading.
        :param size: The amount of data to read.
        :return: The data read from the EWF image.
        """
        self._ewf_handle.seek(offset)
        return self._ewf_handle.read(size)

    def get_size(self):
        """Returns the total size of the EWF image."""
        return self._ewf_handle.get_media_size()


def process_image(image, img_type):
    """
    Processes the given image based on its type.

    :param image: Path to the evidence file.
    :param img_type: Type of the evidence file (raw or ewf).
    :return: Image information object.
    """
    try:
        if img_type == "ewf":
            filenames = pyewf.glob(image)
            ewf_handle = pyewf.handle()
            ewf_handle.open(filenames)
            return EWFImgInfo(ewf_handle)
        else:
            return pytsk3.Img_Info(image)
    except IOError as e:
        print(f"[-] Error processing image file:\n {e}")
        sys.exit(2)


def extract_fs_info(img_info, offset):
    """
    Extracts file system information from the given image info.

    :param img_info: Image information object.
    :param offset: Byte offset for the file system.
    :return: File system object.
    """
    try:
        return pytsk3.FS_Info(img_info, offset)
    except IOError as e:
        print(f"[-] Unable to open file system:\n {e}")
        sys.exit(3)


def create_pdf(table_data, filename):
    """
    Creates a PDF file from the provided table data.

    :param table_data: Data to be included in the PDF.
    :param filename: Name of the PDF file to create.
    """
    pdf = SimpleDocTemplate(filename, pagesize=letter)
    elements = [
        Table(
            table_data,
            style=[
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 2, colors.black),
            ],
        )
    ]
    pdf.build(elements)


def encode_pdf_base64(input_pdf, output_pdf, password):
    """
    Encodes a PDF file in base64 and applies password protection.

    :param input_pdf: Path to the input PDF file.
    :param output_pdf: Path to the output PDF file.
    :param password: Password to protect the PDF file.
    """
    with open(input_pdf, "rb") as file:
        reader = PdfReader(file)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        writer.encrypt(password)

        with open(output_pdf, "wb") as output_file:
            writer.write(output_file)


def generate_directory_table(fs, encode_base64=True):
    """
    Generates a table of directory contents from a file system.

    :param fs: File system object.
    :param encode_base64: Boolean flag to determine if data should be encoded in base64.
    :return: A table with directory contents.
    """
    table = [["Name", "Type", "Size", "Create Date", "Modify Date"]]
    root_dir = fs.open_dir(path="/")
    for f in root_dir:
        if not f.info or not f.info.meta or not f.info.name:
            continue
        name, f_type, size, create, modify = get_file_info(f, encode_base64)
        table.append([name, f_type, size, create, modify])
    return table


def get_file_info(f, encode_base64):
    """
    Extracts file information for table entry.

    :param f: File object from file system.
    :param encode_base64: Boolean flag to determine if name should be encoded in base64.
    :return: Tuple of file information (name, type, size, create date, modify date).
    """
    name = f.info.name.name
    if isinstance(name, bytes) and encode_base64:
        name = base64.b64encode(name).decode()

    f_type = "DIR" if f.info.meta.type == pytsk3.TSK_FS_META_TYPE_DIR else "FILE"
    size = str(f.info.meta.size)
    create = str(f.info.meta.crtime)
    modify = str(f.info.meta.mtime)
    return name, f_type, size, create, modify


def main(image, img_type, password, offset=0, encode_base64=True):
    """
    Main function to process the evidence file.

    :param image: Path to the evidence file.
    :param img_type: Type of the evidence file (raw or ewf).
    :param password: Password for PDF encryption.
    :param offset: Byte offset for the partition (optional).
    :param encode_base64: Boolean flag to determine if data should be encoded in base64.
    """
    print(f"[+] Opening {image}")
    img_info = process_image(image, img_type)
    fs = extract_fs_info(img_info, offset)

    directory_table = generate_directory_table(fs, encode_base64)
    print(tabulate(directory_table, headers="firstrow"))

    pdf_filename = f"{os.path.splitext(os.path.basename(image))[0]}_{datetime.now().strftime('%Y%m%d')}.pdf"
    create_pdf(directory_table, pdf_filename)
    encode_pdf_base64(pdf_filename, f"encoded_{pdf_filename}", password)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Utility to gather open evidence containers"
    )
    parser.add_argument("EVIDENCE_FILE", help="Evidence file path")
    parser.add_argument(
        "TYPE", choices=("raw", "ewf"), help="Type of evidence: raw (dd) or EWF (E01)"
    )
    parser.add_argument(
        "-p", "--password", required=True, help="Password for PDF encryption"
    )
    parser.add_argument(
        "-o", "--offset", type=int, default=0, help="Partition byte offset"
    )
    parser.add_argument(
        "-b", "--base64", action="store_true", help="Encode table data in base64"
    )

    args = parser.parse_args()

    if os.path.exists(args.EVIDENCE_FILE) and os.path.isfile(args.EVIDENCE_FILE):
        main(args.EVIDENCE_FILE, args.TYPE, args.password, args.offset, args.base64)
    else:
        print(
            f"[-] Supplied input file {args.EVIDENCE_FILE} does not exist or is not a file"
        )
        sys.exit(1)
