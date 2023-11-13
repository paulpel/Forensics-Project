import os
import sys
import pytsk3

class Forensics:

    def __init__(self) -> None:
        self.disk_path = "DiskImages"
        self.file_formats = ["E01", "dmg"]
        self.disk_images = self.find_images()
        self.choosen_image = None if not self.disk_images else self.disk_images[0]
        self.options = {
            '1': self.identify_os, 
            '2': self.stub_function,  # Placeholder for actual function
            '3': self.stub_function,  # Placeholder for actual function
            '4': self.stub_function,  # Placeholder for actual function
            '5': self.stub_function,  # Placeholder for actual function
            '6': self.change_disk_image,
            '7': self.quit_application
        }

    def find_images(self):
        found_files = []
        for root, dirs, files in os.walk(self.disk_path):
            for file in files:
                if any(file.endswith('.' + ext) for ext in self.file_formats):
                    found_files.append(os.path.join(root, file))
        return found_files
    
    def print_menu(self):
        choosen_image_text = f"Choosen disk image: {self.choosen_image}" if self.choosen_image else "No disk image selected."
        print(f"""
{choosen_image_text}

Please choose an option:
1. Identify operating system
2. Search for contacts and emails
3. Extract data from documents
4. Analyze visited websites
5. Perform statistical analysis of data
6. Change disk image
7. Exit program
""")

    def identify_os(self):
        if self.choosen_image is None:
            print("No disk image selected.")
            return

        try:
            img = pytsk3.Img_Info(self.choosen_image)
            fs = pytsk3.FS_Info(img)

            # Get the file system type from the image
            fs_type = fs.info.ftype

            # File system type constants mapping from TSK
            fs_type_str_mapping = {
                pytsk3.TSK_FS_TYPE_NTFS: 'NTFS',
                pytsk3.TSK_FS_TYPE_FAT12: 'FAT12',
                pytsk3.TSK_FS_TYPE_FAT16: 'FAT16',
                pytsk3.TSK_FS_TYPE_FAT32: 'FAT32',
                pytsk3.TSK_FS_TYPE_EXT2: 'EXT2',
                pytsk3.TSK_FS_TYPE_EXT3: 'EXT3',
                pytsk3.TSK_FS_TYPE_EXT4: 'EXT4',
                pytsk3.TSK_FS_TYPE_HFS: 'HFS',
                # Add other file system types as needed
            }

            fs_type_str = fs_type_str_mapping.get(fs_type, "Unknown")

            os_identifier = {
                'Windows': ['NTFS', 'FAT12', 'FAT16', 'FAT32'],
                'Linux': ['EXT2', 'EXT3', 'EXT4'],
                'macOS': ['HFS', 'HFS+']
            }

            # Attempt to match the file system type to an OS
            identified_os = "Unknown"
            for os_name, identifiers in os_identifier.items():
                if fs_type_str in identifiers:
                    identified_os = os_name
                    break

            print(f"Identified OS: {identified_os}, FS Type: {fs_type_str}")

        except IOError as e:
            print(f"Cannot open image or filesystem. Error: {e}")

    def change_disk_image(self):
        print("\nAvailable disk images:")
        for index, image in enumerate(self.disk_images, start=1):
            print(f"{index}. {image}")
        print(f"{len(self.disk_images) + 1}. Go back to main menu\n")

        try:
            choice = int(input("Select a disk image number or go back: "))
            if 1 <= choice <= len(self.disk_images):
                self.choosen_image = self.disk_images[choice - 1]
                print(f"\nDisk image changed to {self.choosen_image}")
            elif choice == len(self.disk_images) + 1:
                return
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    
    def quit_application(self):
        print("Closing application...")
        sys.exit(0)
    
    def main_loop(self):
        while True:
            self.print_menu()
            choice = input("Enter the option number: ")
            action = self.options.get(choice)
            if action:
                action()
            else:
                print("Unknown option selected!")

    def stub_function(self):
        print("This functionality is not implemented yet.")
        input("Press Enter to continue...")

if __name__ == "__main__":
    forensic_instance = Forensics()
    forensic_instance.main_loop()
