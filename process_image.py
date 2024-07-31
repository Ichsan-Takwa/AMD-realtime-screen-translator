import cv2
import pytesseract
from pytesseract import Output
import numpy as np
from enum import Enum
import pandas as pd

from PIL import Image, ImageDraw, ImageFont

from transformers import MarianMTModel, MarianTokenizer

src_lang = "en"
tgt_lang = "id"
model_name = f'Helsinki-NLP/opus-mt-{src_lang}-{tgt_lang}'
tokenizer = MarianTokenizer.from_pretrained(model_name)
model = MarianMTModel.from_pretrained(model_name)

class PSM_OPTION(str, Enum):
    """PAGE SEGMENTATION MODE.  Contains
    0   :   Orientation and script detection (OSD) only.
    1   :   Automatic page segmentation with OSD.
    2   :   Automatic page segmentation, but no OSD, or OCR.
    3   :   Fully automatic page segmentation, but no OSD. (Default)
    4   :   Assume a single column of text of variable sizes.
    5   :   Assume a single uniform block of vertically aligned text.
    6   :   Assume a single uniform block of text.
    7   :   Treat the image as a single text line.
    8   :   Treat the image as a single word.
    9   :   Treat the image as a single word in a circle.
    10  :   Treat the image as a single character.
    11  :   Sparse text. Find as much text as possible in no particular order.
    12  :   Sparse text with OSD.
    13  :   Raw line. Treat the image as a single text line, bypassing hacks that are Tesseract-specific."""
    
    psm_0 = r'--psm 0'
    psm_1 = r'--psm 1'
    psm_2 = r'--psm 2'
    psm_3 = r'--psm 3'
    psm_4 = r'--psm 4'
    psm_5 = r'--psm 5'
    psm_6 = r'--psm 6'
    psm_7 = r'--psm 7'
    psm_8 = r'--psm 8'
    psm_9 = r'--psm 9'
    psm_10 = r'--psm 10'
    psm_11 = r'--psm 11'
    psm_12 = r'--psm 12'
    psm_13 = r'--psm 13'

class OEM_OPTION(str, Enum):
    """OCR Engine modes: (see https://github.com/tesseract-ocr/tesseract/wiki#linux)
    0   :   Legacy engine only.
    1   :   Neural nets LSTM engine only.
    2   :   Legacy + LSTM engines.
    3   :   Default, based on what is available."""
    oem_0 = r'--oem 0'
    oem_1 = r'--oem 1'
    oem_2 = r'--oem 2'
    oem_3 = r'--oem 3'
    
    
    

class Tesserract:
    def __init__(self, oem, psm) -> None:
        """Object Character Recognition (OCR)
        extract text data from image using Tesserract OCR Engine

        Parameters
        ----------
        oem : str
            OCR engine mode
        psm : str
            Page segmentation mode"""
        self.tesserract_config = f"{oem} {psm}"
        
    def get_image_text(self,image) -> list:
        image_np = np.array(image)
        # gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
        # Use pytesseract to do OCR on the image
        text = pytesseract.image_to_string(image_np, config=self.tesseract_config)
        content = text.split("\n\n")
        return content
    
    def get_image_data(self, image, tresh=20) -> dict:
        image_np = np.array(image)
        gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
        # Use pytesseract to do OCR on the image
        data = pytesseract.image_to_data(gray, output_type=Output.DATAFRAME, config=self.tesserract_config)
        
        # filter data by confidence level and remove intersected coordinate
        # data = data[(data["conf"] > tresh) * (~data.isna()["text"]) * (data["text"] != " ")].reset_index()
        data = data[data["level"]>=3]
        
        return data
    
def overlay_translated_text(image, ocr:Tesserract):
    image_arr = np.array(image)
    data = ocr.get_image_data(image_arr)
    paragraphs_data = extract_paragraphs(data)
    result = draw_bound_from_imagefrom_data(image_arr, paragraphs_data)
    # print("draw bound image success")
    return result
    
    
# Convert the image to grayscale
def draw_bound_from_imagefrom_data(img, data):
    img = img.copy()
    
    # Define the parameters
    font = cv2.FONT_HERSHEY_DUPLEX
    font_scale = 1
    font_thickness = 2
    color = (0, 255, 0)  # Green
    
    for i in range(len(data["text"])):
        (x, y, w, h) = (data['x'][i], data['y'][i], data['width'][i], data['height'][i])
        cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), -1)
        
        if  data['text'][i].strip():
            # Draw the multiline text on the image
            # img = draw_multiline_text(img, data['text'][i], (x,y,w,h), font, font_scale, font_thickness, color, w)
            # img = draw_multiline_text(img, data['text'][i], (x,y,w,h), font, font_scale, font_thickness, color, w)
            img = add_text_to_image(img, (x, y, w, h), data['text'][i])
    
    return img

def extract_paragraphs(df : pd.DataFrame):
    block_df = df[df['level'] == 3]
    word_df = df[df['level'] == 5]

    paragraphs = []

    # Loop melalui setiap blok paragraf
    for idx, block in block_df.iterrows():
        block_text = ""
        x, y, w, h = block['left'], block['top'], block['width'], block['height']
        
        # Cari semua kata dalam blok ini
        for _, word in word_df.iterrows():
            if (word['left'] >= x
                and word['top'] >= y
                and word['left'] + word['width'] <= x + w
                and word['top'] + word['height'] <= y + h):
                block_text += word['text'] + " "
        
        block_text = block_text.strip()
        paragraphs.append({'text': block_text, 'x': x, 'y': y, 'width': w, 'height': h})

        # Buat DataFrame dari hasil
    paragraphs_df = pd.DataFrame(paragraphs, columns=['text', 'x', 'y', 'width', 'height'])

    return paragraphs_df

    
def draw_multiline_text(image, text, coords, font, font_scale, font_thickness, color, max_width):
    x, y, w, h = coords

    # Split the text into lines that fit within the max_width
    words = text.split()
    lines = []
    current_line = words[0]

    for word in words[1:]:
        # Calculate the width of the current line with the new word
        (line_width, _), _ = cv2.getTextSize(current_line + ' ' + word, font, font_scale, font_thickness)
        if line_width <= max_width:
            current_line += ' ' + word
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)  # Add the last line

    # Calculate the height of the text block to adjust the font size if necessary
    text_height = (len(lines) * cv2.getTextSize(lines[0], font, font_scale, font_thickness)[0][1]) * 1.2

    if text_height > h:
        # Adjust the font scale to fit the text within the given height
        font_scale = font_scale * (h / text_height)

    y_offset = y

    for line in lines:
        (line_width, line_height), _ = cv2.getTextSize(line, font, font_scale, font_thickness)
        y_offset += line_height
        if y_offset > y + h:  # Stop if the text exceeds the height of the box
            break
        # Draw the text line
        cv2.putText(image, line, (x, y_offset), font, font_scale, color, font_thickness, lineType=cv2.LINE_AA)
        y_offset += int(line_height * 0.2)  # Add some space between lines

    return image


def add_text_to_image(image_array, coordinates, text):
    """
    Menambahkan teks ke dalam gambar sesuai dengan koordinat yang diberikan.

    Parameters:
    - image_array: numpy array dari gambar
    - coordinates: tuple (x, y, w, h) yang menentukan area untuk teks
    - text: teks yang akan ditambahkan ke gambar

    Returns:
    - Gambar dengan teks yang ditambahkan
    """
    # Konversi array numpy ke PIL Image
    image = Image.fromarray(image_array)
    draw = ImageDraw.Draw(image)
    
    # Ekstrak koordinat
    x, y, w, h = coordinates
    if w > image.width-80:
        return image_array

    # Tentukan ukuran font awal
    font_size = 100  # Ukuran awal yang besar untuk kemudian disesuaikan
    font_path = "arial.ttf"  # Pastikan font path tersedia

    while font_size > 0:
        font = ImageFont.truetype(font_path, font_size)
        lines = []
        words = text.split()
        current_line = []

        for word in words:
            current_line.append(word)
            line_width = draw.textbbox((0, 0), ' '.join(current_line), font=font)[2]
            if line_width > w:
                current_line.pop()
                lines.append(' '.join(current_line))
                current_line = [word]

        lines.append(' '.join(current_line))
        total_height = sum(draw.textbbox((0, 0), line, font=font)[3] for line in lines)

        if total_height <= h:
            break

        font_size -= 1

    # Gambarkan setiap baris teks ke dalam gambar
    y_text = y
    for line in lines:
        draw.text((x, y_text), line, font=font, fill=(255, 255, 255))
        y_text += draw.textbbox((0, 0), line, font=font)[3]
        
    
    return np.array(image)

def translate_text(text):

    
    translated = model.generate(**tokenizer(text, return_tensors="pt", padding=True))
    return tokenizer.decode(translated[0], skip_special_tokens=True)
