from __future__ import print_function
import argparse
import os
import pytsk3
import pyewf
from tabulate import tabulate
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table
from PyPDF2 import PdfReader, PdfWriter
from datetime import datetime
from pdf2image import convert_from_path
import tempfile
from reportlab.lib import colors
from reportlab.platypus import TableStyle
import base64
from reportlab.pdfgen import canvas
from PyPDF2 import PageObject
from PyPDF2 import PdfWriter
from PIL import ImageDraw, ImageFont
import pytz

__description__ = (
    "Script to process and extract data from forensic evidence containers."
)


class EWFImgInfo(pytsk3.Img_Info):
    """
    Class to handle EWF (Expert Witness Format) image files using pytsk3 library.

    :param ewf_handle: A handle to an EWF file opened using pyewf.
    :type ewf_handle: pyewf.handle
    """

    def __init__(self, ewf_handle):
        self._ewf_handle = ewf_handle
        super(EWFImgInfo, self).__init__(url="", type=pytsk3.TSK_IMG_TYPE_EXTERNAL)

    def close(self):
        """
        Closes the EWF handle.
        """
        self._ewf_handle.close()

    def read(self, offset, size):
        """
        Reads a specified amount of data from a specific offset in the EWF image file.

        :param offset: The offset from which to start reading in the EWF image file.
        :type offset: int
        :param size: The amount of data to read, in bytes.
        :type size: int
        :returns: The data read from the specified offset in the EWF image.
        :rtype: bytes
        :raises IOError: If there's an error reading from the file at the specified offset.

        This method seeks to the given offset in the EWF image file and reads the specified amount of data.
        It's useful for extracting specific segments of data from large EWF images. The method returns the data
        as a bytes object, which can then be processed further as needed.
        """
        self._ewf_handle.seek(offset)
        return self._ewf_handle.read(size)

    def get_size(self):
        """
        Gets the total size of the EWF image.

        :return: The size of the EWF image.
        """
        return self._ewf_handle.get_media_size()


def main(image, img_type, part_type, password, encode_base64=True):
    """
    Processes an evidence file, extracts metadata, and creates an encrypted PDF report.

    :param image: Path to the evidence file.
    :type image: str
    :param img_type: Type of the evidence file, either 'raw' or 'ewf'.
    :type img_type: str
    :param part_type: Type of partition. Optional, provide if known.
    :type part_type: str, optional
    :param password: Password for encrypting the generated PDF.
    :type password: str
    :param encode_base64: Flag to determine if names should be encoded in base64. Defaults to True.
    :type encode_base64: bool
    :returns: None
    :raises IOError: If there's an error in processing the EWF format or reading the partition table or file system.

    This function opens and processes an evidence file. Depending on the file type, it extracts relevant
    metadata, which is then used to generate an encrypted PDF report. The function handles both raw and EWF
    (Expert Witness Format) files and supports optional partition type specification. If 'encode_base64' is True,
    certain data elements are encoded in base64 in the PDF report. The function also handles errors related to
    invalid file format or inaccessible file system/partition table.
    """
    print("[+] Opening {}".format(image))
    if img_type == "ewf":
        try:
            filenames = pyewf.glob(image)
        except IOError as e:
            print("[-] Invalid EWF format:\n {}".format(e))
            return

        ewf_handle = pyewf.handle()
        ewf_handle.open(filenames)
        header_table, hash_table = e01_metadata(ewf_handle)

        img_info = EWFImgInfo(ewf_handle)
    else:
        img_info = pytsk3.Img_Info(image)

    volume = None
    fs = None

    try:
        if part_type:
            attr_id = getattr(pytsk3, "TSK_VS_TYPE_" + part_type)
            volume = pytsk3.Volume_Info(img_info, attr_id)
        else:
            fs = pytsk3.FS_Info(img_info)
    except IOError as e:
        print("[-] Unable to read partition table or file system:\n {}".format(e))
        return

    if volume:
        part_metadata(volume)
    elif fs:
        # Handle file system analysis if needed
        pass
    else:
        print("No partition or file system detected.")

    if volume:
        table_1, table_2 = part_metadata(volume)
    elif fs:
        # Handle file system analysis if needed
        pass
    else:
        print("No partition or file system detected.")

    timezone = pytz.timezone("Europe/Warsaw")
    date_str = datetime.now(timezone).strftime("%Y_%m_%d_%H_%M_%S")
    pdf_filename = f"meta_{os.path.splitext(os.path.basename(image))[0]}_{date_str}.pdf"
    create_encrypted_pdf(
        table_1,
        table_2,
        header_table,
        hash_table,
        pdf_filename,
        password,
        encode_base64,
    )


def create_encrypted_pdf(
    table_1, table_2, header_table, hash_table, filename, password, encode_base64=False
):
    """
    Creates an encrypted PDF file containing various data tables. The tables can optionally be encoded in base64.

    :param table_1: Data for the first table.
    :type table_1: list of lists
    :param table_2: Data for the second table.
    :type table_2: list of lists
    :param header_table: Data for the header table.
    :type header_table: list of lists
    :param hash_table: Data for the hash table.
    :type hash_table: list of lists
    :param filename: Path to save the encrypted PDF.
    :type filename: str
    :param password: Password for encrypting the PDF.
    :type password: str
    :param encode_base64: Option to encode table data in base64. Default is False.
    :type encode_base64: bool
    :returns: None
    :raises: (Include any relevant exceptions this function might raise)

    This function first creates tables from the provided data, which are then compiled into a PDF document.
    If 'encode_base64' is True, the data in the tables is encoded in base64 before being added to the PDF.
    After the PDF is created, it is encrypted using the provided password.
    """

    pdf = SimpleDocTemplate(filename, pagesize=letter)
    elements = []

    # Define table styles
    table_style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]
    )

    # Function to encode table data in base64
    def encode_table_data(table_data):
        return [
            [base64.b64encode(str(cell).encode()).decode() for cell in row]
            for row in table_data
        ]

    if encode_base64:
        # Encode table data in base64
        table_1 = encode_table_data(table_1)
        table_2 = encode_table_data(table_2)
        header_table = encode_table_data(header_table)
        hash_table = encode_table_data(hash_table)

    # Create tables
    table_1_table = Table(table_1, style=table_style)
    table_2_table = Table(table_2, style=table_style)
    header_table = Table(header_table, style=table_style)
    hash_table = Table(hash_table, style=table_style)

    # Adjust column widths to fit content if encode_base64 is True

    # Append tables to elements
    elements.append(table_1_table)
    elements.append(table_2_table)
    elements.append(header_table)
    elements.append(hash_table)

    # Build PDF
    pdf.build(elements)

    # Encrypt PDF
    encrypt_pdf(filename, password)


def encrypt_pdf(input_pdf, password):
    """
    Converts a given PDF into an encrypted, timestamped version with watermarked pages.

    :param input_pdf: Path to the input PDF file to be encrypted.
    :type input_pdf: str
    :param password: Password to be used for encrypting the PDF.
    :type password: str
    :returns: None
    :raises IOError: If there's an error in processing the input PDF or writing the output file.

    This function first converts the input PDF into individual images. It then creates a watermark
    (consisting of a timestamp) on each image. Each watermarked image is converted back to a PDF format
    and added to a new PDF file. This new PDF is then encrypted with the provided password. The function
    overwrites the original input file with the encrypted version. The timestamp is based on the current
    date and time in the Europe/Warsaw timezone.
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


def part_metadata(vol):
    """
    Extracts and returns metadata of partitions from a given volume information object.

    :param vol: The volume information object, usually obtained from a forensic image.
    :type vol: VolumeInfo object or similar
    :returns: Two tables containing partition metadata. The first table lists indices and types,
              while the second lists offset starts and lengths of each partition.
    :rtype: tuple(list, list)
    :raises ValueError: If the provided volume information is None or invalid.

    This function processes volume information from a forensic image and extracts metadata
    about the partitions present in it. The metadata includes indices, types, offset starts,
    and lengths of each partition. This data is organized into two separate tables and returned.
    If the volume information is not available or invalid, a warning is printed, and the function
    returns nothing.
    """
    if vol is None:
        print("No volume information available.")
        return

    table_1 = [["Index", "Type"]]
    for part in vol:
        table_1.append([part.addr, part.desc.decode("utf-8")])

    table_2 = [["Offset Start (Sectors)", "Length (Sectors)"]]
    for part in vol:
        table_2.append([part.start, part.len])

    return table_1, table_2


def e01_metadata(e01_image):
    """
    Extracts and returns metadata from an EWF (E01) image file, formatted into tables.

    :param e01_image: The EWF image object from which metadata is to be extracted.
    :type e01_image: EWFImage object or similar
    :returns: Two tables containing the metadata of the EWF image. The first table includes
              header fields and their values, and the second table includes hash values.
    :rtype: tuple(list, list)

    This function processes an EWF (E01) image and extracts its metadata, including header
    values and hash values. This metadata is organized into two tables: one for header fields
    and another for hash values related to the acquisition of the image. The function returns
    these tables for further processing or display. It's specifically tailored for EWF (E01)
    image files, commonly used in digital forensics.
    """
    headers = e01_image.get_header_values()
    hashes = e01_image.get_hash_values()

    # Create a table for header values
    header_table = [["Header Field", "Value"]]
    for k in headers:
        header_table.append([k, headers[k]])

    # Create a table for hash values
    hash_table = [["Acquisition", "Value"]]
    for h in hashes:
        hash_table.append(["Acquisition " + h, hashes[h]])

    return header_table, hash_table


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__description__)
    parser.add_argument("EVIDENCE_FILE", help="Evidence file path")
    parser.add_argument("TYPE", help="Type of Evidence", choices=("raw", "ewf"))
    parser.add_argument(
        "-p", help="Partition Type", choices=("DOS", "GPT", "MAC", "SUN")
    )
    parser.add_argument("-f", "--filename", help="Output PDF filename", required=True)
    parser.add_argument(
        "-pwd", "--password", help="Password for the PDF", required=True
    )
    parser.add_argument(
        "-b", "--base64", action="store_true", help="Encode table data in base64"
    )
    args = parser.parse_args()

    if os.path.exists(args.EVIDENCE_FILE) and os.path.isfile(args.EVIDENCE_FILE):
        main(args.EVIDENCE_FILE, args.TYPE, args.p, args.base64)
    else:
        print(
            "[-] Supplied input file {} does not exist or is not a file".format(
                args.EVIDENCE_FILE
            )
        )
