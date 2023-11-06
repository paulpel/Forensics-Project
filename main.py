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
            '1': self.identify_os,  # Placeholder for actual function
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
            # Open the disk image
            img = pytsk3.Img_Info(self.choosen_image)
            # Open the file system
            fs = pytsk3.FS_Info(img)
            
            # Define paths that could give us a hint about the OS
            paths_to_check = {
                'Windows': ['/Windows/System32/config', '/Windows/System32'],
                'Linux': ['/etc/os-release', '/etc/issue'],
                # Add other OS-specific paths here
            }
            
            # Check each path for each OS type
            for os_name, paths in paths_to_check.items():
                for path in paths:
                    try:
                        f = fs.open_dir(path=path)
                    except IOError:
                        continue
                    else:
                        print(f"Found {path}. This is likely a {os_name} system.")
                        return  # Exit the function if OS is identified
            
            print("\nOperating system could not be identified.")

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
