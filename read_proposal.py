import PyPDF2
import sys

try:
    reader = PyPDF2.PdfReader("/Users/ravindubandara/Desktop/smart_city/Final_year_Project_Proposal (2).pdf")
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    print(text)
except Exception as e:
    print(f"Error: {e}")
