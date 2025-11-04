import tkinter as tk
from pathlib import Path
from tkinter import filedialog

file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
print(file_path)
cc = Path(file_path).name.rstrip('pdf')
print(cc)
co = Path(cc).name.rstrip('.')
print(co)
stem = Path(file_path).stem
print(stem)