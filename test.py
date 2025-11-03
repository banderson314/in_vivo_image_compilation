import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from datetime import datetime
import re
import math
import os
import pandas as pd
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageTk
import warnings
warnings.filterwarnings("ignore", message=".*pin_memory.*")
import subprocess
def get_reader():
	"""Return a persistent EasyOCR reader, loading it only once."""
	if not hasattr(get_reader, "reader"):
		print("Loading EasyOCR")
		import easyocr
		get_reader.reader = easyocr.Reader(['en'], verbose=False, gpu=False)
		print("EasyOCR is loaded")
	return get_reader.reader

# Allowed image extensions
image_extensions = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}


"""
Updates you should consider including:

An extra optional dialog box with additional settings such as margin size etc.
The ability to show multiple dates
What if you gave the option to have a black background?
"""


def user_defined_settings():
	def on_close_window():
		root.destroy()
		exit()

	class DirectoryFrame(tk.Frame):
		def __init__(self, parent):
			super().__init__(parent)
			self.rows = []

			# Add the first row initially
			self.add_row()

		def add_row(self, text=""):
			row_index = len(self.rows)

			# Label
			if row_index == 0:
				label = tk.Label(self, text="Image directory:")
				label.grid(row=row_index, column=0, padx=5, pady=0)

			# Entry widget
			entry = tk.Entry(self, width=30)
			entry.grid(row=row_index, column=1, padx=5, pady=0)
			entry.bind("<KeyRelease>", self.on_entry_change)

			# Choose directory button
			button = tk.Button(self, text="Choose", 
							command=lambda e=entry: self.choose_directory(entry_widget=e))
			button.grid(row=row_index, column=2, padx=5, pady=0)

			# cSLO checkbox
			cslo_var = tk.BooleanVar(value=False)
			cslo_cb = tk.Checkbutton(self, text="cSLO", variable=cslo_var,
									command=lambda e=entry: self.checkbox_toggle(e, 'cslo'))
			cslo_cb.grid(row=row_index, column=3, padx=5, pady=0)

			# OCT checkbox
			oct_var = tk.BooleanVar(value=False)
			oct_cb = tk.Checkbutton(self, text="OCT", variable=oct_var,
									command=lambda e=entry: self.checkbox_toggle(e, 'oct'))
			oct_cb.grid(row=row_index, column=4, padx=5, pady=0)

			# Store the row info
			self.rows.append({
				'entry': entry,
				'cslo_var': cslo_var,
				'oct_var': oct_var,
				'cslo_cb': cslo_cb,
				'oct_cb': oct_cb,
				'button': button
			})

		def cleanup_empty_rows(self):
			# Keep the last row, delete other empty rows
			new_rows = []
			for i, row in enumerate(self.rows):
				if i == len(self.rows) - 1 or row['entry'].get().strip() != "":
					new_rows.append(row)
				else:
					# Remove widgets from grid
					for widget in ['entry', 'cslo_cb', 'oct_cb', 'button']:
						row[widget].grid_forget()
			self.rows = new_rows

			# Re-grid all remaining rows so their row numbers match their list indices
			for i, row in enumerate(self.rows):
				row['entry'].grid(row=i, column=1, padx=5, pady=0)
				row['button'].grid(row=i, column=2, padx=5, pady=0)
				row['cslo_cb'].grid(row=i, column=3, padx=5, pady=0)
				row['oct_cb'].grid(row=i, column=4, padx=5, pady=0)

			# Update the number of mice
			number_of_mice_frame.mice_set.clear()
			number_of_mice_frame.figure_out_how_many_mice()




		def checkbox_toggle(self, entry_widget, which):
			row = next(r for r in self.rows if r['entry'] == entry_widget)
			if which == 'cslo' and row['cslo_var'].get():
				row['oct_var'].set(False)
			elif which == 'oct' and row['oct_var'].get():
				row['cslo_var'].set(False)


		def on_entry_change(self, event):
			entry_widget = event.widget
			row_index = next(i for i, r in enumerate(self.rows) if r['entry'] == entry_widget)

			# If last row is non-empty, add a new blank row
			if row_index == len(self.rows) - 1 and entry_widget.get().strip() != "":
				self.add_row()
			
			# Remove extra empty rows
			self.cleanup_empty_rows()

			def check_directory(directory):
				cslo_or_oct_directory = ""

				# List contents of the directory
				contents = os.listdir(directory)

				# Filter out directories and files
				subdirs = [os.path.join(directory, d) for d in contents if os.path.isdir(os.path.join(directory, d))]
				files = [f for f in contents if os.path.isfile(os.path.join(directory, f))]

				# cSLO images: Check if each subdir contains "OS" and "OD"
				if subdirs:
					valid = True
					for subdir in subdirs:
						if not (os.path.isdir(os.path.join(subdir, "OS")) or os.path.isdir(os.path.join(subdir, "OD"))):
							valid = False
							break
					if valid:
						cslo_or_oct_directory = "cslo"
						return cslo_or_oct_directory

				# OCT images: Check if the directory contains image files
				# Get all files in directory (ignores subdirectories themselves)
				files = [f for f in os.listdir(inputted_directory) 
						if os.path.isfile(os.path.join(inputted_directory, f))]

				# Look for image files with "_OD_" or "_OS_" in the filename
				for f in files:
					ext = os.path.splitext(f)[1].lower()
					if ext in image_extensions and ("_OD_" in f or "_OS_" in f):
						cslo_or_oct_directory = "oct"
						return cslo_or_oct_directory

				return cslo_or_oct_directory

			inputted_directory = entry_widget.get()
			if os.path.exists(inputted_directory):
				# Change the text color to black
				entry_widget.config(fg="black")

				# Determine if the images are cSLO or OCT and update the checkbox accordingly
				cslo_or_oct_directory = check_directory(inputted_directory)
				
				if cslo_or_oct_directory == "cslo":
					row = next(r for r in self.rows if r['entry'] == entry_widget)
					row['cslo_var'].set(True)
					row['oct_var'].set(False)
				elif cslo_or_oct_directory == "oct":
					row = next(r for r in self.rows if r['entry'] == entry_widget)
					row['oct_var'].set(True)
					row['cslo_var'].set(False)

				# Update the number of mice
				number_of_mice_frame.figure_out_how_many_mice()

				# Update the availabe images the user can select (e.g. "BAF", "OCT vertical", etc.)
				images_to_use_frame.determine_what_images_are_available()
			

			# If this isn't a directory that exists, change the color to red
			else:
				entry_widget.config(fg="red")

		def choose_directory(self, row_index=None, entry_widget=None):
			directory = filedialog.askdirectory()
			if directory:
				if entry_widget is not None:
					# Find the row by entry widget
					row = next(r for r in self.rows if r['entry'] == entry_widget)
				else:
					row = self.rows[row_index]
				
				row['entry'].delete(0, tk.END)
				row['entry'].insert(0, directory)
				self.on_entry_change(event=type('Event', (), {'widget': row['entry']})())

		def get_data(self):
			directories = []
			for row in self.rows:
				path = row['entry'].get().strip()
				if os.path.exists(path):
					if path:  # skip blanks
						if row['cslo_var'].get():
							image_type = "cslo"
						elif row['oct_var'].get():
							image_type = "oct"
						else:
							image_type = None

						directories.append((path, image_type))
			
			return {"directories": directories}

	class NumberOfMiceFrame(tk.Frame):
		def __init__(self, parent):
			super().__init__(parent)
			self.mice_set = set()

			text_label = tk.Label(self, text="Number of mice found:")
			text_label.grid(row=0, column=0, padx=5)

			number_of_mice = 0
			mouse_number_label = tk.Label(self, text=number_of_mice)
			mouse_number_label.grid(row=0, column=1, padx=5)

			#determine_button = tk.Button(self, text="Determine", command=self.figure_out_how_many_mice)
			#determine_button.grid(row=0, column=2, padx=5)

		def figure_out_how_many_mice(self):
			directory_info_from_user = directory_frame.get_data().get("directories")
			
			for entry in directory_info_from_user:
				directory_path, image_type = entry

				if image_type == "oct":
					
					for file in os.listdir(directory_path):
						ext = os.path.splitext(file)[1].lower()
						if ext in image_extensions:
							mouse_number = file.split("_")[0]
							self.mice_set.add(mouse_number)
					
				elif image_type == "cslo":
					for item in os.listdir(directory_path):
						subfolder_path = os.path.join(directory_path, item)
						
						# Check if it is a directory
						if os.path.isdir(subfolder_path):
							# Get a list of items inside this subfolder
							sub_items = os.listdir(subfolder_path)
							
							# Check if both "OD" and "OS" exist as folders
							if "OD" in sub_items and "OS" in sub_items:
								od_path = os.path.join(subfolder_path, "OD")
								os_path = os.path.join(subfolder_path, "OS")
								
								# Make sure both are directories, not files
								if os.path.isdir(od_path) and os.path.isdir(os_path):
									self.mice_set.add(item)
		
			number_of_mice = len(self.mice_set)
			self.update_mouse_number(number_of_mice)

		def update_mouse_number(self, number_of_mice):
			mouse_number_label = tk.Label(self, text=number_of_mice)
			mouse_number_label.grid(row=0, column=1, padx=5)
			
			# Update the row x column numbers
			row_col_frame.update_numbers(number_of_mice)

			# Update the mouse dataframe
			mouse_info_frame.on_entry_change()
		
		def get_data(self):
			return {
				"mice_numbers_set": self.mice_set
			}


	class MouseInfoFrame(tk.Frame):
		def __init__(self, parent):
			super().__init__(parent)

			self.create_blank_df()

			label = tk.Label(self, text="Mouse info:")
			label.grid(row=0, column=0, padx=5, pady=0)

			# StringVar linked to Entry
			self.excel_var = tk.StringVar()			
			self.excel_var.trace_add("write", self.on_entry_change)

			self.excel_entry = tk.Entry(self, textvariable=self.excel_var, width=42)
			self.excel_entry.insert(0, "[Mouse info file location]")
			self.excel_entry.grid(row=0, column=1, padx=5, pady=0)

			choose_button = tk.Button(self, text="Choose", command=self.choose_file)
			choose_button.grid(row=0, column=2, padx=5, pady=0)

			edit_button = tk.Button(self, text="Edit info", command=self.edit_mouse_info)
			edit_button.grid(row=0, column=3, padx=5, pady=0)

			cslo_labID_button = tk.Button(self, text="Determine lab ID based off of cSLO images",
								  command=self.determine_cslo_labID_number)
			cslo_labID_button.grid(row=1, column=0, columnspan=4, padx=5, pady=3)

		def choose_file(self):
			info_file_path = filedialog.askopenfilename(
				filetypes=[("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv")]
			)
			if info_file_path:
				self.excel_var.set(info_file_path)
			
		def on_entry_change(self, *args):
			self.create_blank_df()
			self.add_mice_from_csv_doc()
			self.add_mice_from_image_files()

		def create_blank_df(self):
			self.df = pd.DataFrame(columns=[
				"cSLO number",
				"Lab ID",
				"Cage number",
				"Treatment group",
				"Exclude images"
			])

		def add_mice_from_csv_doc(self):
			file_path = self.excel_var.get()
			if os.path.isfile(file_path):
				ext = os.path.splitext(file_path)[1]  # get file extension

				new_df = None
				if ext in [".xlsx", ".xls"]:
					new_df = pd.read_excel(file_path)
				elif ext == ".csv":
					new_df = pd.read_csv(file_path)

				if new_df is not None and not new_df.empty:
					new_df["Exclude images"] = new_df["Exclude images"].map(lambda x: True if x == "X" else False)
					self.df = pd.concat([self.df, new_df], ignore_index=True)
				

		def add_mice_from_image_files(self):
			# Including mouse numbers found in the files not in the excel spreadsheet
			for mouse in number_of_mice_frame.mice_set:
				if mouse not in self.df["cSLO number"].values:
					# Create a new row with cSLO number set and other columns empty/NaN
					new_row = {
						"cSLO number": mouse,
						"Lab ID": "",
						"Cage number": "",
						"Treatment group": "",
						"Exclude images": False
					}
					self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)


		def edit_mouse_info(self):
			top = tk.Toplevel(root)
			top.title("Edit DataFrame")

			entries = {}  # store references to Entry widgets or BooleanVars for checkboxes

			# Column headers
			for j, col in enumerate(self.df.columns):
				label = tk.Label(top, text=col, font=("Arial", 10, "bold"))
				label.grid(row=0, column=j, padx=2, pady=5)

			# Data rows
			for i, row in self.df.iterrows():
				for j, col in enumerate(self.df.columns):
					if col == "Exclude images":
						# Use a checkbox for boolean values
						var = tk.BooleanVar(value=row[col])
						cb = tk.Checkbutton(top, variable=var)
						cb.grid(row=i+1, column=j, padx=0, pady=0)
						entries[(i, col)] = var  # store the BooleanVar
					else:
						# Text entry, centered
						e = tk.Entry(top, justify="center")
						e.grid(row=i+1, column=j, padx=2, pady=0)
						e.insert(0, row[col])
						entries[(i, col)] = e

			def save_changes():
				for (i, col), widget in entries.items():
					if col == "Exclude images":
						# Get the value of the checkbox
						self.df.at[i, col] = widget.get()
					else:
						self.df.at[i, col] = widget.get()
				top.destroy()

			save_button = tk.Button(top, text="Save", command=save_changes)
			save_button.grid(row=len(self.df)+1, column=0, columnspan=len(self.df.columns), pady=10)
			
		def determine_cslo_labID_number(self):
			# Get a list of directories that have cSLO images
			data_dic = directory_frame.get_data()
			available_directories = data_dic["directories"]	# Will be a list of tuples: (directory, "cslo"/"oct")
			cslo_directories = []
			for directory, image_type in available_directories:
				if image_type == "cslo":
					cslo_directories.append(directory)
			
			if len(cslo_directories) == 0:
				print("No cSLO directories found")
				return
			
			# Going through the cSLO image directories and grabbing the information from the images and putting it in the df
			for directory in cslo_directories:
				self.cslo_ear_tag_dic = determine_ear_tag_number_in_cslo_images(directory)
				for cslo_num, et_value in self.cslo_ear_tag_dic.items():
					# check if the cSLO number exists in the df
					if cslo_num in self.df["cSLO number"].values:
						# update the Lab ID
						self.df.loc[self.df["cSLO number"] == cslo_num, "Lab ID"] = et_value
					else:
						# add a new row
						new_row = {"cSLO number": cslo_num, "Lab ID": et_value}
						self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
			self.edit_mouse_info()


		def get_data(self):
			self.df_to_export = self.df
			
			# Remove any mice that there aren't any image files of
			self.df_to_export = self.df_to_export[self.df_to_export["cSLO number"].isin(number_of_mice_frame.mice_set)]

			# Remove any mice that were marked to be excluded
			self.df_to_export = self.df_to_export[self.df_to_export["Exclude images"] != True]

			# Create dictionary with cSLO numbers (key) and [Lab ID, cage, group]
			mouse_info_dic = {
				row["cSLO number"]: (row["Lab ID"], row["Cage number"], row["Treatment group"])
				for _, row in self.df_to_export.iterrows()
			}

			return {
				"mouse_info_dic": mouse_info_dic
			}



	class TitleFrame(tk.Frame):
		def __init__(self, parent):
			super().__init__(parent)
			self.columnconfigure(1, weight=1)

			# Title label + entry
			title_label = tk.Label(self, text="Title:")
			title_label.grid(row=0, column=0, padx=5, pady=0, sticky="w")

			self.title_entry = tk.Entry(self, width=40)
			self.title_entry.insert(0, "In vivo imaging")
			self.title_entry.grid(row=0, column=1, padx=5, pady=0, sticky="we")

			# Subtitle label + entry
			subtitle_label = tk.Label(self, text="Subtitle:")
			subtitle_label.grid(row=1, column=0, padx=5, pady=0, sticky="w")

			today_str = datetime.today().strftime("%B %d, %Y").replace(" 0", " ")
			self.subtitle_entry = tk.Entry(self, width=40)
			self.subtitle_entry.insert(0, today_str)
			self.subtitle_entry.grid(row=1, column=1, padx=5, pady=0, sticky="we")

		def get_data(self):
			return {
				"document_title": self.title_entry.get(),
				"subtitle": self.subtitle_entry.get()
			}
				


	class RowColumnFrame(tk.Frame):
		def __init__(self, parent):
			super().__init__(parent)

			self.number_of_mice = 0

			# Calculate initial row/col numbers
			number_of_rows, number_of_columns = self.determine_row_and_column_number(self.number_of_mice)

			# Label
			label = tk.Label(self, text="Row x column:")
			label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

			# Row entry
			self.row_entry = tk.Entry(self, width=5)
			self.row_entry.insert(0, number_of_rows)
			self.row_entry.grid(row=0, column=1, padx=5, pady=5)

			# x label
			x_label = tk.Label(self, text="x")
			x_label.grid(row=0, column=2, padx=5, pady=5)

			# Column entry
			self.column_entry = tk.Entry(self, width=5)
			self.column_entry.insert(0, number_of_columns)
			self.column_entry.grid(row=0, column=3, padx=5, pady=5)

			# Bind updates
			self.row_entry.bind("<KeyRelease>", self.update_columns)
			self.column_entry.bind("<KeyRelease>", self.update_rows)

		# Triggered when other things happen in the dialog box
		def update_numbers(self, new_total_number):
			self.number_of_mice = new_total_number
			number_of_rows, number_of_columns = self.determine_row_and_column_number(self.number_of_mice)
			self.row_entry.delete(0, tk.END)
			self.row_entry.insert(0, str(number_of_rows))
			self.column_entry.delete(0, tk.END)
			self.column_entry.insert(0, str(number_of_columns))

		@staticmethod
		def determine_row_and_column_number(total_number):
			square_root = math.sqrt(total_number)
			number_of_rows = math.floor(square_root)
			number_of_columns = math.ceil(square_root)
			if number_of_rows == number_of_columns:
				number_of_rows -= 1
				number_of_columns += 1
			while number_of_rows * number_of_columns < total_number:
				number_of_rows += 1
			if number_of_rows == number_of_columns:
				number_of_rows -= 1
				number_of_columns += 1
			return number_of_rows, number_of_columns

		# Triggered when row number is changed
		def update_columns(self, *_):
			try:
				row_number = self.row_entry.get()
				if row_number != "":
					row_number = int(row_number)
					column_number = math.ceil(self.number_of_mice / row_number)
					self.column_entry.delete(0, tk.END)
					self.column_entry.insert(0, str(column_number))
			except ValueError:
				self.column_entry.delete(0, tk.END)

		# Triggered when column number is changed
		def update_rows(self, *_):
			try:
				column_number = self.column_entry.get()
				if column_number != "":
					column_number = int(column_number)
					row_number = math.ceil(self.number_of_mice / column_number)
					self.row_entry.delete(0, tk.END)
					self.row_entry.insert(0, str(row_number))
			except ValueError:
				self.row_entry.delete(0, tk.END)

		
		def get_data(self):
			return {
				"number_of_rows": int(self.row_entry.get()),
				"number_of_columns": int(self.column_entry.get())
			}


	class NumberAndCsloCropFrame(tk.Frame):
		def __init__(self, parent):
			super().__init__(parent)

			# Use label
			mouse_label_to_use_label = tk.Label(self, text="Use:")
			mouse_label_to_use_label.grid(row=0, column=0, padx=5, pady=0, sticky="w")

			# cSLO checkbox
			self.cslo_number_var = tk.BooleanVar(value=True)
			cslo_cb = tk.Checkbutton(self, text="cSLO numbers", variable=self.cslo_number_var)
			cslo_cb.grid(row=0, column=1, padx=5, pady=0, sticky="w")

			# Lab ID checkbox
			self.labID_var = tk.BooleanVar(value=False)
			labID_cb = tk.Checkbutton(self, text="Lab IDs", variable=self.labID_var)
			labID_cb.grid(row=0, column=2, padx=5, pady=0, sticky="w")

			# Crop cSLO text checkbox
			self.crop_cslo_text_var = tk.BooleanVar(value=True)
			crop_cslo_text_cb = tk.Checkbutton(self, text="Crop the text off of cSLO images",
											variable=self.crop_cslo_text_var)
			crop_cslo_text_cb.grid(row=1, column=0, columnspan=3, padx=5, pady=0, sticky="w")

		def get_data(self):
			self.cslo_number_bool = self.cslo_number_var.get()
			self.labID_bool = self.labID_var.get()
			self.crop_cslo_text_bool = self.crop_cslo_text_var.get()

			return {
				"cslo_number_bool": self.cslo_number_bool,
				"labID_bool": self.labID_bool,
				"crop_cslo_text_bool": self.crop_cslo_text_bool
			}

	
	class OctCropFrame(tk.Frame):
		def __init__(self, parent):
			super().__init__(parent)

			# Crop OCT section
			self.oct_crop_var = tk.BooleanVar(value=False)
			oct_crop_cb = tk.Checkbutton(self, text="Crop OCT images",
										variable=self.oct_crop_var,
										command=self.oct_crop_checkbox)
			oct_crop_cb.grid(row=2, column=0, padx=5, pady=0, sticky="w")

			self.oct_crop_entry = tk.Entry(self, width=5, state="disabled")
			self.oct_crop_entry.grid(row=2, column=1, padx=0, pady=0)

			pixel_label = tk.Label(self, text="pixels")
			pixel_label.grid(row=2, column=2, padx=0, pady=0)

			oct_crop_button = tk.Button(self, text="Find minimum OCT height", command=self.find_minimum_oct_height)
			oct_crop_button.grid(row=2, column=3, padx=5, pady=0)

		def oct_crop_checkbox(self):
			if self.oct_crop_var.get():
				self.oct_crop_entry.config(state="normal")
				
				# -- Figure out the height of OCT images, if any --
				# Find OCT directories
				directories_info = directory_frame.get_data()
				directories = directories_info["directories"]
				oct_directory_present = False
				for directory in directories:
					if directory[1] == "oct":
						oct_directory_present = True
						oct_directory = directory[0]
						continue
				if oct_directory_present:
					# list all files
					files = sorted(os.listdir(oct_directory))
					image_height = 0
					# find the first file that looks like an image
					for f in files:
						if f.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp')):
							image_path = os.path.join(oct_directory, f)
							with Image.open(image_path) as img:
								_, image_height = img.size
					if image_height > 0:
						self.oct_crop_entry.delete(0, tk.END)
						self.oct_crop_entry.insert(0, image_height)
					else:
						self.oct_crop_entry.insert(0, "480")

			else:
				self.oct_crop_entry.delete(0, tk.END)
				self.oct_crop_entry.config(state="disabled")
		

		def find_minimum_oct_height(self):
			oct_heights = []

			self.available_directories = directory_frame.get_data()["directories"]

			for directory in self.available_directories:
				if directory[1] == "oct":
					directory_path = directory[0]
				else:
					continue
			
				image_files = [
					f for f in os.listdir(directory_path)
					if f.lower().endswith(tuple(image_extensions)) and os.path.isfile(os.path.join(directory_path, f))
				]

				for image_file in image_files:
					# Only including images if the user hasn't removed them
					cslo_number = image_file.split("_")[0]
					if cslo_number in mouse_info_frame.get_data()["mouse_info_dic"]:
						image_path = os.path.join(directory_path, image_file)
						image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
						top, bottom = find_oct_retina_bounds(image)
						height = abs(bottom-top)
						oct_heights.append(height)
			
			if len(oct_heights) > 0:
				self.smallest_possible_height = max(oct_heights)
				self.oct_crop_entry.delete(0, tk.END)
				self.oct_crop_entry.insert(0, self.smallest_possible_height)
			else:
				self.oct_crop_entry.delete(0, tk.END)


			return

			# Reporting what image requires the greatest height
			for directory in self.available_directories:
				if directory[1] == "oct":
					directory_path = directory[0]
				else:
					continue
			
				image_files = [
					f for f in os.listdir(directory_path)
					if f.lower().endswith(tuple(image_extensions)) and os.path.isfile(os.path.join(directory_path, f))
				]

				for image_file in image_files:
					image_path = os.path.join(directory_path, image_file)
					image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
					top, bottom = find_oct_retina_bounds(image)
					height = abs(bottom-top)
					if height == self.smallest_possible_height:
						print(image_path)
						print(f"Top: {top}. Bottom: {bottom}.")


		def get_data(self):
			oct_height = self.oct_crop_entry.get()

			return {
				"oct_height": oct_height
			}


	class ImagesToUseFrame(tk.Frame):
		def __init__(self, parent):
			super().__init__(parent)

			title = tk.Label(self, text="Images to use and the order they are arranged in:")
			title.grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=(2,5))

			# --- Main area: Available | Selected side by side ---
			main_frame = tk.Frame(self)
			main_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=(17,5))
			main_frame.columnconfigure(0, weight=1)
			main_frame.columnconfigure(1, weight=1)

			# Available list
			available_frame = tk.Frame(main_frame)
			available_frame.grid(row=0, column=0, sticky="new", padx=(0, 15))

			tk.Label(available_frame, text="Available image types").grid(row=0, column=0, sticky="w")
			self.available_listbox = tk.Listbox(available_frame, selectmode="browse", height=1, width=25)
			self.available_listbox.grid(row=1, column=0, sticky="nsew", pady=3)
			self.available_listbox.bind("<Double-Button-1>", self.add_selected_from_listbox)
			self.available_listbox.config(selectbackground="SystemHighlight", activestyle="none")

			# Scrollbar (initially hidden)
			self.available_scrollbar = tk.Scrollbar(available_frame, orient="vertical")
			self.available_listbox.config(yscrollcommand=self.available_scrollbar.set)
			self.available_scrollbar.config(command=self.available_listbox.yview)

			# Selected list (container with draggable rows)
			selected_frame = tk.Frame(main_frame)
			selected_frame.grid(row=0, column=1, sticky="nsew")
			#selected_frame.rowconfigure(1, weight=1)

			tk.Label(selected_frame, text="Selected images (rename or reorder)").grid(row=0, column=0, sticky="w")
			self.selected_frame = tk.Frame(selected_frame)
			self.selected_frame.grid(row=1, column=0, sticky="nsew")

			self.available_image_types = []
			self.selected_image_types = []
			self.rows = []
			self.drag_data = None

			
		# --- Populate available options ---
		def determine_what_images_are_available(self):
			directories = directory_frame.get_data()["directories"]
			self.available_image_types_set = set()

			for directory, image_type in directories:
				if image_type == "oct":
					image_files = [
						f for f in os.listdir(directory)
						if os.path.isfile(os.path.join(directory, f))
						and os.path.splitext(f)[1].lower() in image_extensions
					]
					for image_file in image_files:
						oct_type = "OCT " + image_file.split("_")[2]
						self.available_image_types_set.add(oct_type)
				
				elif image_type =="cslo":
					image_files = []
					
					# Grabbing all cSLO file names
					for subdir, dirs, files in os.walk(directory):
						if os.path.basename(subdir) in {"OD", "OS"}:
							for f in files:
								if os.path.splitext(f)[1].lower() in image_extensions:
									image_files.append(f)
					
					cslo_images_dic = {}
					for image in image_files:
						image_base = os.path.splitext(image)[0]
						image_number, mouse_number, eye, image_type = image_base.split("_")
						mouse_eye = mouse_number + "_" + eye

						if mouse_eye not in cslo_images_dic:
							cslo_images_dic[mouse_eye] = {}

						if image_type not in cslo_images_dic[mouse_eye]:
							cslo_images_dic[mouse_eye][image_type] = 0

						cslo_images_dic[mouse_eye][image_type] += 1
					
					max_counts = {}
					for mouse_eye, counts in cslo_images_dic.items():
						for image_type, count in counts.items():
							if image_type not in max_counts or count > max_counts[image_type]:
								max_counts[image_type] = count

					def ordinal(n):
						if 10 <= n % 100 <= 20:
							suffix = "th"
						else:
							suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
						return f"{n}{suffix}"

					for image_type, count in max_counts.items():
						image_type = "cSLO " + image_type
						if int(count) == 1:
							self.available_image_types_set.add(image_type)
						else:
							self.available_image_types_set.discard(image_type)
							i = 0
							for i in range(int(count)):
								image_type_ammended = f"{image_type} ({ordinal(i+1)})"
								self.available_image_types_set.add(image_type_ammended)
								self.available_image_types_set.add(f"{image_type} [select]")
						


			self.available_image_types = sorted(list(self.available_image_types_set))
			self.refresh_available_list()


		def refresh_available_list(self):
			"""Update available listbox items and manage scrollbar visibility."""
			# Clear listbox
			self.available_listbox.delete(0, tk.END)
			
			# Create a set of the original names already selected
			selected_originals = {orig for orig, _ in self.selected_image_types}

			# Insert items that are not yet selected
			for item in self.available_image_types:
				if item not in selected_originals:
					self.available_listbox.insert(tk.END, item)

			# Adjust height
			num_items = self.available_listbox.size()
			self.available_listbox.config(height=min(num_items, 10))  # max height = 10

			# Show or hide scrollbar
			if num_items > 10:
				self.available_scrollbar.grid(row=1, column=1, sticky="ns")
			else:
				self.available_scrollbar.grid_forget()


		# --- Add/Remove logic ---
		def add_selected_from_listbox(self, event=None):
			selection = self.available_listbox.curselection()
			if not selection:
				return
			
			value = self.available_listbox.get(selection[0])
			self.available_listbox.delete(selection[0])
			self.selected_image_types.append((value, value))  # (original, current/custom)
			self.add_label_row(value)

			# Refresh available list to update height and scrollbar
			self.refresh_available_list()



		def add_label_row(self, selection):
			frame = tk.Frame(self.selected_frame)
			frame.grid(sticky="ew", pady=0)
			frame.columnconfigure(1, weight=1)

			handle = tk.Label(frame, text="≡", font=("Arial", 10), cursor="fleur")
			handle.grid(row=0, column=0, padx=(0,2), pady=0)
			handle.bind("<Button-1>", self.start_drag)
			handle.bind("<B1-Motion>", self.do_drag)
			handle.bind("<ButtonRelease-1>", self.stop_drag)

			label = tk.Label(frame, text=selection, anchor="w")
			label.grid(row=0, column=1, sticky="ew", pady=0)

			remove_btn = tk.Button(frame, text="✕", relief="flat", bd=0,
								command=lambda f=frame, s=selection: self.remove_row(f, s))
			remove_btn.grid(row=0, column=3, padx=(2,0), pady=0)


			# Determining initial custom name
			custom_name = selection
			if custom_name[:5] == "cSLO ":
				custom_name = custom_name[5:]
			elif custom_name[:4] == "OCT ":
				custom_name = custom_name[4:]
			if custom_name[-9:] == " [select]":
				custom_name = custom_name[:-9]
			ordinal_format = r" \(\d+(st|nd|rd|th)\)$"
			custom_name = re.sub(ordinal_format, "", custom_name)
			custom_name = custom_name[0].upper() + custom_name[1:]

			image_type_name_var = tk.StringVar(value=custom_name)
			entry_box = tk.Entry(frame, textvariable=image_type_name_var, width=15)
			entry_box.grid(row=0, column=2, padx=(5,0))

			# Update self.selected_image_types when entry changes
			def on_entry_change(*args):
				for i, (orig, custom) in enumerate(self.selected_image_types):
					if orig == selection:
						self.selected_image_types[i] = (orig, image_type_name_var.get())
						break

			image_type_name_var.trace_add("write", on_entry_change)
			on_entry_change()	# Force initial update


			self.rows.append((frame, selection))
			self.repack_rows()



		def remove_row(self, frame, selection):
			for i, (f, sel) in enumerate(self.rows):
				if f == frame:
					f.destroy()
					del self.rows[i]
					break

			# remove from selected_image_types (match by first element)
			self.selected_image_types = [
				pair for pair in self.selected_image_types if pair[0] != selection
			]

			self.refresh_available_list()
			self.repack_rows()




		def repack_rows(self):
			for i, (f, _) in enumerate(self.rows):
				f.grid(row=i, column=0, sticky="ew", pady=0)


		# --- Drag & reorder logic ---
		def start_drag(self, event):
			widget = event.widget.master
			self.drag_data = {
				"widget": widget,
				"start_y": event.y_root,
				"orig_index": self.get_row_index(widget),
				"original_colors": {
					widget: widget.cget("bg"),
					**{child: child.cget("bg") for child in widget.winfo_children()}
					}
			}
			widget.lift()
			widget.config(bg="#929292")
			for child in widget.winfo_children():
				child.config(bg="#929292")

		def do_drag(self, event):
			if not self.drag_data:
				return
			widget = self.drag_data["widget"]
			y = event.y_root
			widget.lift()

			hover_index = None
			for i, (f, _) in enumerate(self.rows):
				if f == widget:
					continue
				fy = f.winfo_rooty()
				fh = f.winfo_height()
				if fy < y < fy + fh:
					hover_index = i
					break

			current_index = self.get_row_index(widget)
			if hover_index is not None and hover_index != current_index:
				self.rows.insert(hover_index, self.rows.pop(current_index))
				self.selected_image_types.insert(hover_index, self.selected_image_types.pop(current_index))
				self.repack_rows()


		def stop_drag(self, event):
			widget = event.widget.master
			original_colors = self.drag_data["original_colors"]

			# Restore frame color
			if widget in original_colors:
				widget.config(bg=original_colors[widget])

			# Restore each child’s color
			for child in widget.winfo_children():
				if child in original_colors:
					child.config(bg=original_colors[child])
			self.drag_data = None


		def get_row_index(self, frame):
			for i, (f, _) in enumerate(self.rows):
				if f == frame:
					return i
			return None


		def get_data(self):
			return {"images_to_use": self.selected_image_types}



	class PresetFrame(tk.Frame):
		def __init__(self, parent):
			super().__init__(parent)

			label = tk.Label(self, text="Presets")
			label.grid(row=0, column=0, padx=5)


	class ConfirmationFrame(tk.Frame):
		def __init__(self, parent):
			super().__init__(parent)
			
			# Preview layout
			preview_layout_button = tk.Button(self, text="Preview layout", 
									 command=self.preview_layout)
			preview_layout_button.grid(row=0, column=0, padx=5)

			# Preview layout + images
			preview_layout_images_button = tk.Button(self, text="Preview layout & images",
											command=self.preview_layout_and_images)
			preview_layout_images_button.grid(row=0, column=1, padx=5)

			# Okay button
			okay_button = tk.Button(self, text="Okay", command=self.on_ok_click)
			okay_button.grid(row=0, column=2, padx=5)

		def preview_layout(self):
			print("Hello")

		
		def preview_layout_and_images(self):
			self.test_settings = row_col_frame.get_data()
			

		
		def on_ok_click(self):
			self.settings = {}

			self.settings.update(directory_frame.get_data())
			self.settings.update(title_frame.get_data())
			self.settings.update(row_col_frame.get_data())
			self.settings.update(mouse_info_frame.get_data())
			self.settings.update(number_and_cslo_crop_frame.get_data())
			self.settings.update(oct_crop_frame.get_data())
			self.settings.update(images_to_use_frame.get_data())



			root.destroy()



	root = tk.Tk()
	root.title("Settings")
	root.protocol("WM_DELETE_WINDOW", on_close_window)
	root.columnconfigure(0, weight=1)
	root.rowconfigure(0, weight=1)

	directory_frame = DirectoryFrame(root)
	directory_frame.pack(anchor='w')
	number_of_mice_frame = NumberOfMiceFrame(root)
	number_of_mice_frame.pack(anchor='w')
	mouse_info_frame = MouseInfoFrame(root)
	mouse_info_frame.pack(anchor='w', pady=3)
	title_frame = TitleFrame(root)
	title_frame.pack(anchor='w', fill='x')
	row_col_frame = RowColumnFrame(root)
	row_col_frame.pack(anchor='w')
	number_and_cslo_crop_frame = NumberAndCsloCropFrame(root)
	number_and_cslo_crop_frame.pack(anchor='w')
	oct_crop_frame = OctCropFrame(root)
	oct_crop_frame.pack(anchor='w')
	images_to_use_frame = ImagesToUseFrame(root)
	images_to_use_frame.pack(anchor='w')
	preset_frame = PresetFrame(root)
	preset_frame.pack(anchor='w')
	confirmation_frame = ConfirmationFrame(root)
	confirmation_frame.pack(anchor='s', pady=10)

	root.mainloop()
	return confirmation_frame.settings




def determine_ear_tag_number_in_cslo_images(base_directory):
	reader = get_reader()
	cslo_ear_tag_dic = {}

	# loop through all subfolders
	for folder in os.listdir(base_directory):
		folder_path = os.path.join(base_directory, folder)
		if not os.path.isdir(folder_path):
			continue  # skip non-folders

		# prefer "OD", fallback to "OS"
		target_dir = os.path.join(folder_path, "OD")
		if not os.path.exists(target_dir):
			target_dir = os.path.join(folder_path, "OS")
		if not os.path.exists(target_dir):
			continue # skip if it doesn't have the OD or OS subfolders

		# find first image file in target_dir
		files = [f for f in os.listdir(target_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.tif'))]
		if not files:
			continue	# skip if no images

		first_image_path = os.path.join(target_dir, files[0])
		img = cv2.imread(first_image_path)

		if img is None:
			continue	# skip if can't read image

		height, width, _ = img.shape

		# crop bottom-left region
		top_square_height = width
		bottom_rect_height = height - top_square_height
		crop_height = (bottom_rect_height // 3) + 10
		crop_width = int(width * 0.70)  # left 70% of image

		# slice: rows (y), columns (x)
		cropped = img[top_square_height : top_square_height + crop_height, 0:crop_width]

		# OCR
		results = reader.readtext(cropped)
		mouse_id = [res[1] for res in results]  # res[1] contains detected text
		mouse_id_string = " ".join(mouse_id)
		if folder in mouse_id_string:
			ear_tag_number = mouse_id_string.split(folder, 1)[1]
		else:
			ear_tag_number = mouse_id_string
			print(f"Folder ({folder}) not found in {mouse_id_string}")	
		#ear_tag_number = mouse_id_string.split(folder, 1)[1] if folder in mouse_id_string else mouse_id_string
		ear_tag_number = ear_tag_number.replace("_", " ").replace(",", " "). replace(".", " ")
		ear_tag_number = " ".join(ear_tag_number.split()).strip()

		cslo_ear_tag_dic[folder] = ear_tag_number
	
	return(cslo_ear_tag_dic)



def find_oct_retina_bounds(img):
	"""Return the topmost and bottommost pixel positions of the retina."""
	# Convert to grayscale if needed
	if img.ndim == 3:
		img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

	# Flatten along width (take max across columns) to get brightness by row
	#row_max = img.max(axis=1).astype(float)
	row_brightness = np.percentile(img, 95, axis=1).astype(float)

	# Compute adaptive threshold based on overall brightness
	mean = np.mean(img)
	std = np.std(img)
	cutoff = max(mean + std, 50)

	# Find where the retina (bright region) exists
	#bright_rows = np.where(row_max > cutoff)[0]
	bright_rows = np.where(row_brightness > cutoff)[0]

	if bright_rows.size == 0:
		return img.shape[0], 0  # nothing bright enough found

	# Return absolute top and bottom of the bright region
	top = int(bright_rows.min())
	bottom = int(bright_rows.max())
	return top, bottom


settings = user_defined_settings()
for key, value in settings.items():
	print(f"{key}: {value}")

print("")
print(settings)


def compile_images(settings):
	# Unpack settings
	directories = settings["directories"]
	cslo_directories = []
	oct_directories = []
	for directory, image_type in directories:
		if image_type == "cslo":
			cslo_directories.append(directory)
		elif image_type == "oct":
			oct_directories.append(directory)
	document_title = settings["document_title"]
	subtitle = settings["subtitle"]
	number_of_rows = settings["number_of_rows"]
	number_of_columns = settings["number_of_columns"]
	mouse_info_dic = settings["mouse_info_dic"]
	cslo_number_bool = settings["cslo_number_bool"]
	labID_bool = settings["labID_bool"]
	crop_cslo_text_bool = settings["crop_cslo_text_bool"]
	oct_height = settings["oct_height"]
	images_to_use = settings["images_to_use"]

	background_color = (255, 255, 255)
	text_color = (0, 0, 0)
	completed_file_path = "C:/Users/bran314/Desktop/cSLO image compilation images/image_compilation.jpg"


	# Get a list if all images to be used
	cslo_image_file_paths = []
	for directory in cslo_directories:
		mice = [f for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f))]
		mice_directories = []
		
		# Excluding any mice that the user may have manually removed
		for mouse in mice:
			if mouse in mouse_info_dic:
				mice_directories.append(os.path.join(directory, mouse))
		
		for mouse_directory in mice_directories:
			for root, dirs, files in os.walk(mouse_directory):	# recursively walk all subfolders
				folder_name = os.path.basename(root)
				if folder_name in ("OD", "OS"):
					for f in files:
						if f.lower().endswith(tuple(image_extensions)):
							cslo_image_file_paths.append(os.path.join(root, f))
	
		
	oct_image_file_paths = []
	for directory in oct_directories:
		potential_oct_image_files = [f for f in os.listdir(directory)
					 if f.lower().endswith(tuple(image_extensions))]
		
		for file in potential_oct_image_files:
			if file.split("_")[0] in mouse_info_dic:
				oct_image_file_paths.append(os.path.join(directory, file))
	
	if not cslo_image_file_paths and not oct_image_file_paths:
		print("No images are found. Exiting program.")
		exit()




	# Determine the size of the compilation document
	if cslo_image_file_paths:
		example_image = Image.open(cslo_image_file_paths[0])
	else:
		example_image = Image.open(oct_image_file_paths[0])
	image_width = example_image.width
	image_height = example_image.height

	###### Consider making these sizes proportional to your image sizes? #######
	column_margin_size = 45
	row_margin_size = 400

	x_offset = 400
	compilation_width = number_of_columns * (image_width * 2 + column_margin_size) + x_offset 

	y_offset = 700
	if document_title == "":
		y_offset -= 250
		subtitle_y = 35
	else:
		subtitle_y = 230
	if subtitle == "":
		y_offset -= 70
	compilation_height = (image_height * 2 * number_of_rows) + ((number_of_rows - 1) * row_margin_size) + y_offset + 100
	compilation_height = int(compilation_height)
	compiled_image = Image.new('RGB', (compilation_width, compilation_height), background_color)


	# Creating a title for the document
	draw = ImageDraw.Draw(compiled_image)
	text_color = (0, 0, 0)
	title_font = ImageFont.load_default(size=160)
	draw.text((30, 20), document_title, fill=text_color, font=title_font)

	# Creating a subtitle for the document
	title_font = ImageFont.load_default(size=90)
	draw.text((30, subtitle_y), subtitle, fill=text_color, font=title_font)



	# Saving the final product
	compiled_image.save(completed_file_path)

	return completed_file_path


exit()
#completed_file_path = compile_images(settings)



# Opening the final product
if os.name == 'nt':  # Check if the operating system is Windows
	os.startfile(completed_file_path)
	exit()
try:
	subprocess.Popen(['xdg-open', completed_file_path])  # Opens on Linux systems
except OSError:
	try:
		subprocess.Popen(['open', completed_file_path])  # Opens on macOS
	except OSError:
		exit()