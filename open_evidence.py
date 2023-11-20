import argparse
import os
import pytsk3
import pyewf
import sys
from tabulate import tabulate
import base64
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from PyPDF2 import PdfReader, PdfWriter

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
        Reads data from the EWF image file.

        :param offset: The offset from which to start reading.
        :param size: The amount of data to read.
        :return: The data read from the EWF image.
        """
        self._ewf_handle.seek(offset)
        return self._ewf_handle.read(size)

    def get_size(self):
        """
        Gets the total size of the EWF image.

        :return: The size of the EWF image.
        """
        return self._ewf_handle.get_media_size()

def main(image, img_type, offset):
    """
    Main function to process the evidence file.

    :param image: Path to the evidence file.
    :param img_type: Type of the evidence file (raw or ewf).
    :param offset: Byte offset for the partition (optional).
    """
    print(f"[+] Opening {image}")
    if img_type == "ewf":
        try:
            filenames = pyewf.glob(image)
            ewf_handle = pyewf.handle()
            ewf_handle.open(filenames)
            img_info = EWFImgInfo(ewf_handle)
        except IOError as e:
            print(f"[-] Invalid EWF format:\n {e}")
            sys.exit(2)
    else:
        img_info = pytsk3.Img_Info(image)

    if offset is None:
        offset = 0

    try:
        fs = pytsk3.FS_Info(img_info, offset)
    except IOError as e:
        print(f"[-] Unable to open FS:\n {e}")
        sys.exit(3)

    directory_table = generate_directory_table(fs)
    print(tabulate(directory_table, headers="firstrow"))
    pdf_filename = "directory_table.pdf"
    create_pdf(directory_table, pdf_filename)

    encoded_pdf_filename = "encoded_directory_table.pdf"
    password = "YourPassword"
    encode_pdf_base64(pdf_filename, encoded_pdf_filename, password)


def create_pdf(table_data, filename):
    """
    Creates a PDF file from the provided table data.

    :param table_data: Data to be included in the PDF.
    :param filename: Name of the PDF file to create.
    """
    pdf = SimpleDocTemplate(filename, pagesize=letter)
    elements = []

    t = Table(table_data)
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                           ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
                           ('ALIGN',(0,0),(-1,-1),'CENTER'),
                           ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                           ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                           ('BACKGROUND',(0,1),(-1,-1),colors.beige),
                           ('GRID',(0,0),(-1,-1),2,colors.black)]))
    elements.append(t)
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


def generate_directory_table(fs):
    """
    Generates a table of directory contents from a file system.

    :param fs: File system object.
    :return: A table with directory contents.
    """
    table = [["Name", "Type", "Size", "Create Date", "Modify Date"]]
    root_dir = fs.open_dir(path="/")
    for f in root_dir:
        if not f.info or not f.info.meta or not f.info.name:
            continue
        name = f.info.name.name
        f_type = "DIR" if f.info.meta.type == pytsk3.TSK_FS_META_TYPE_DIR else "FILE"
        size = f.info.meta.size
        create = f.info.meta.crtime
        modify = f.info.meta.mtime
        table.append([name, f_type, size, create, modify])
    return table


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Utility to gather open evidence containers")
    parser.add_argument("EVIDENCE_FILE", help="Evidence file path")
    parser.add_argument("TYPE", help="Type of evidence: raw (dd) or EWF (E01)", choices=("raw", "ewf"))
    parser.add_argument("-o", "--offset", help="Partition byte offset", type=int)

    args = parser.parse_args()

    if os.path.exists(args.EVIDENCE_FILE) and os.path.isfile(args.EVIDENCE_FILE):
        main(args.EVIDENCE_FILE, args.TYPE, args.offset)
    else:
        print(f"[-] Supplied input file {args.EVIDENCE_FILE} does not exist or is not a file")
        sys.exit(1)
