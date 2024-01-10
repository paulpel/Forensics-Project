import argparse
import os
import sys
import pytsk3
import pyewf
import base64
from tabulate import tabulate
from reportlab.lib.pagesizes import letter
from PIL import Image
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table
from reportlab.lib import colors
from PyPDF2 import PdfReader, PdfWriter
from datetime import datetime
from reportlab.pdfgen import canvas
from pdf2image import convert_from_path
import tempfile
from PIL import ImageDraw
import pytz


class EWFImgInfo(pytsk3.Img_Info):
    """
    A subclass of pytsk3.Img_Info that specifically handles EWF (Expert Witness Format) image files.

    This class provides methods to interact with EWF images, such as reading data from the image,
    getting its size, and closing the file handle. It uses the pyewf library to handle EWF files.

    :param ewf_handle: A handle to an EWF file opened using the pyewf library.
    :type ewf_handle: pyewf.handle
    """

    def __init__(self, ewf_handle):
        """
        Initializes the EWFImgInfo object with a given EWF file handle.

        :param ewf_handle: A handle to an EWF file.
        :type ewf_handle: pyewf.handle
        """
        self._ewf_handle = ewf_handle
        super(EWFImgInfo, self).__init__(url="", type=pytsk3.TSK_IMG_TYPE_EXTERNAL)

    def close(self):
        """
        Closes the EWF handle.

        This method should be called to properly close the EWF file when it's no longer needed.
        """
        self._ewf_handle.close()

    def read(self, offset, size):
        """
        Reads a specific amount of data from the EWF image starting at a given offset.

        :param offset: The offset in the EWF image from which to start reading.
        :type offset: int
        :param size: The number of bytes to read from the offset.
        :type size: int
        :return: The data read from the EWF image.
        :rtype: bytes

        This method is used to read a segment of data from the EWF image. It's essential for
        parsing and analyzing the contents of the image.
        """
        self._ewf_handle.seek(offset)
        return self._ewf_handle.read(size)

    def get_size(self):
        """
        Retrieves the total size of the EWF image.

        :return: The size of the EWF image in bytes.
        :rtype: int

        This method returns the total size of the EWF image, which is useful for understanding
        the scope of the data contained within.
        """
        return self._ewf_handle.get_media_size()


def process_image(image, img_type):
    """
    Processes a given disk image based on its type (raw or EWF).

    :param image: Path to the evidence disk image file.
    :type image: str
    :param img_type: Type of the disk image ('raw' or 'ewf').
    :type img_type: str
    :return: An object containing information about the disk image.
    :rtype: EWFImgInfo or Img_Info
    :raises IOError: If there's an error in processing the image file.

    This method processes the disk image file specified by the 'image' parameter. It handles
    both raw and EWF (Expert Witness Format) image types. For EWF images, it opens the image
    using pyewf and returns an EWFImgInfo object. For raw images, it returns a pytsk3.Img_Info object.
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
    Extracts file system information from an image info object at a given byte offset.

    :param img_info: Image information object.
    :type img_info: EWFImgInfo or Img_Info
    :param offset: Byte offset for the file system in the image.
    :type offset: int
    :return: File system object.
    :rtype: FS_Info
    :raises IOError: If unable to open the file system at the specified offset.

    This method takes an image information object and extracts the file system information
    from it, starting at the specified byte offset. This is typically used for disk images
    that contain a file system, enabling further analysis and data extraction.
    """
    try:
        return pytsk3.FS_Info(img_info, offset)
    except IOError as e:
        print(f"[-] Unable to open file system:\n {e}")
        sys.exit(3)


def create_pdf(table_data, filename):
    """
    Creates a PDF file from the provided table data.

    :param table_data: Data to be included in the PDF as a table.
    :type table_data: list of list
    :param filename: Name and path of the PDF file to create.
    :type filename: str
    :returns: None

    This method generates a PDF file from the given table data. The data is formatted
    as a table in the PDF. This is useful for presenting extracted data in a structured,
    readable format.
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


def encode_pdf(input_pdf, password):
    """
    Encrypts and watermarks a PDF file.

    :param input_pdf: Path to the input PDF file to be encrypted and watermarked.
    :type input_pdf: str
    :param password: Password to be used for encrypting the PDF.
    :type password: str
    :returns: None
    :raises IOError: If there's an error in processing or writing the PDF file.

    This method converts each page of a PDF file into an image, adds a watermark with
    the current date and time, and then reassembles these images back into a PDF. It
    then encrypts the PDF file with the given password. This is useful for securing and
    timestamping sensitive PDF documents.
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
        width, height = image.size
        x = width / 2
        y = height / 2

        draw = ImageDraw.Draw(image)
        text = f"Timestamp: \n {current_datetime}"
        draw.text(
            (10, 10), text=text, fill=(185, 185, 185), fontsize=64
        )  # Adjust position and color as needed

        # Create a temporary PDF file for each image
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            image.save(temp_pdf, format="PDF")

            # Add the temporary PDF page to the PDF writer
            pdf_writer.append(temp_pdf.name)

    # Apply password protection
    pdf_writer.encrypt(password)

    # Write the encrypted PDF to the output file
    with open(input_pdf, "wb") as output_file:
        pdf_writer.write(output_file)


def generate_directory_table(fs, encode_base64=True):
    """
    Generates a table of directory contents from a file system.

    :param fs: File system object to extract directory information from.
    :type fs: FS_Info
    :param encode_base64: Whether to encode data in base64. Defaults to True.
    :type encode_base64: bool
    :return: A table containing directory contents.
    :rtype: list of list

    This method creates a table with directory contents, including file names, types,
    sizes, and creation/modification dates, from a given file system. The table data
    can be optionally encoded in base64.
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
    Extracts and returns file information for a given file object.

    :param f: File object from which to extract information.
    :type f: File object
    :param encode_base64: Flag to determine if the file name should be base64 encoded.
    :type encode_base64: bool
    :return: Tuple containing file information (name, type, size, creation date, modification date).
    :rtype: tuple

    This method extracts information from a file object, including the file's name, type, size,
    and creation and modification dates. The file name can be optionally encoded in base64.
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
    Main function to process an evidence file and generate a PDF report.

    :param image: Path to the evidence file.
    :type image: str
    :param img_type: Type of the evidence file ('raw' or 'ewf').
    :type img_type: str
    :param password: Password for encrypting the PDF report.
    :type password: str
    :param offset: Byte offset for the partition, if applicable. Defaults to 0.
    :type offset: int, optional
    :param encode_base64: Flag to determine if data should be base64 encoded. Defaults to True.
    :type encode_base64: bool
    :returns: None

    This function processes an evidence file, extracting file system information and generating
    a directory table. It then creates a PDF report from this table, which is encrypted and
    optionally base64 encoded. This function serves as the main entry point for processing
    disk images and generating reports.
    """
    print(f"[+] Opening {image}")
    img_info = process_image(image, img_type)
    fs = extract_fs_info(img_info, offset)

    directory_table = generate_directory_table(fs, encode_base64)
    timezone = pytz.timezone("Europe/Warsaw")
    pdf_filename = f"{os.path.splitext(os.path.basename(image))[0]}_{datetime.now(timezone).strftime('%Y_%m_%d__%H_%M_%S')}.pdf"
    create_pdf(directory_table, pdf_filename)
    encode_pdf(pdf_filename, password)


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
