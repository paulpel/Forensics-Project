import os
import sys
import pyewf
import pytsk3
import argparse
from open_evidence import main as open_evidence_main
from evidence_metadata import main as evidence_metadata_main

class Forensics:

	def __init__(self) -> None:
		self.disk_path = "DiskImages"
		self.file_formats = ["E01", "dmg", "001", "raw", "dd"]
		self.disk_images = self.find_images()
		self.choosen_image = ""
		self.password = "default_password"
		self.encode_base64 = True
		self.options = {
			'1': self.choose_disk_image, 
			'2': self.change_disk_image,
			'3': self.extract_info,
			'4': self.extract_metadata, 
			'5': self.change_password,
			'6': self.toggle_base64_encoding,
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
		img_name = self.choosen_image.split("/")[-1]
		choosen_image_text = f"Choosen disk image: {img_name}" if self.choosen_image else "No disk image selected."
		print(f"""
{choosen_image_text}

Please choose an option:
1. Choose disk image
2. Change disk image
3. Extract information about documents
4. Extract metadata
5. Change Password (Current: {self.password})
6. Toggle Base64 Encoding (Current: {'Enabled' if self.encode_base64 else 'Disabled'})
7. Exit program
""")
			
	def choose_disk_image(self):
		if self.choosen_image != "":
			print("\nYou have already have chosen the image.")
			return
		else:
			print("\nAvailable disk images:")
			for index, image in enumerate(self.disk_images, start=1):
				img_name = image.split("/")[-1]
				print(f"{index}. {img_name}")
			print(f"{len(self.disk_images) + 1}. Go back to main menu\n")

			try:
				choice = int(input("Select a disk image number or go back: "))
				if 1 <= choice <= len(self.disk_images):
					self.choosen_image = self.disk_images[choice - 1]
					img_name = self.choosen_image.split("/")[-1]
					print(f"\nSelected disk image: {img_name}")
				elif choice == len(self.disk_images) + 1:
					return
				else:
					print("Invalid selection. Please try again.")
			except ValueError:
				print("Invalid input. Please enter a number.")

	def change_disk_image(self):
		if self.choosen_image == "":
			print("Choose the image first.")
			self.choose_disk_image()
		else:
			print("\nAvailable disk images:")
			for index, image in enumerate(self.disk_images, start=1):
				img_name = image.split("/")[-1]
				print(f"{index}. {img_name}")
			print(f"{len(self.disk_images) + 1}. Go back to main menu\n")

			try:
				choice = int(input("Select a disk image number or go back: "))
				if 1 <= choice <= len(self.disk_images):
					if self.disk_images[choice - 1] == self.choosen_image:
						print("\nYou have already have chosen this image.")
						return
					else:
						self.choosen_image = self.disk_images[choice - 1]
						img_name = self.choosen_image.split("/")[-1]
						print(f"\nChanged disk image to {img_name}")
				elif choice == len(self.disk_images) + 1:
					return
				else:
					print("Invalid selection. Please try again.")
			except ValueError:
				print("Invalid input. Please enter a number.")

	def change_password(self):
		new_password = input("Enter new password: ")
		self.password = new_password
		print("Password changed successfully.")

	def toggle_base64_encoding(self):
		self.encode_base64 = not self.encode_base64
		print(f"Base64 Encoding {'enabled' if self.encode_base64 else 'disabled'}.")

	def extract_info(self):
		print("[+] Extracting information about documents...")
		print(self.choosen_image)

		if not self.choosen_image or not self.choosen_image.endswith((".E01", ".raw", ".dd")):
			print("[-] Invalid or no image selected. Choose a valid E01 or raw image first.")
			self.choose_disk_image()
			print("here")
			return
		try:
			# Parse arguments for the main2.py script only
			parser = argparse.ArgumentParser(description="Utility to gather data from evidence containers")
			parser.add_argument("-o", "--offset", help="Partition byte offset", type=int)

			args, _ = parser.parse_known_args()

			# Call the function from open_evidence.py
			open_evidence_main(self.choosen_image, "ewf" if self.choosen_image.endswith(".E01") else "raw", password=self.password, encode_base64=self.encode_base64)

		except Exception as e:
			print(f"[-] Error extracting information:\n {e}")

	def extract_metadata(self):
		print("[+] Extracting metadata from the disk image...")

		if not self.choosen_image or not self.choosen_image.endswith((".E01", ".raw", ".dd")):
			print("[-] Invalid or no image selected. Choose a valid E01 or raw image first.")
			self.choose_disk_image()
			return

		# Present partition type choices to the user
		print("\nChoose the partition type:")
		partition_types = ["DOS", "GPT", "MAC", "SUN"]
		for index, p_type in enumerate(partition_types, start=1):
			print(f"{index}. {p_type}")
		print(f"{len(partition_types) + 1}. Cancel")

		try:
			choice = int(input("Enter your choice: "))
			if 1 <= choice <= len(partition_types):
				selected_partition_type = partition_types[choice - 1]
				print(f"Selected partition type: {selected_partition_type}")
			elif choice == len(partition_types) + 1:
				print("Metadata extraction cancelled.")
				return
			else:
				print("Invalid selection. Please try again.")
				return
		except ValueError:
			print("Invalid input. Please enter a number.")
			return

		try:
			evidence_metadata_main(
				self.choosen_image, 
				"ewf" if self.choosen_image.endswith(".E01") else "raw", 
				part_type=selected_partition_type, 
				password=self.password
			)
		except Exception as e:
			print(f"[-] Error extracting metadata:\n {e}")

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
