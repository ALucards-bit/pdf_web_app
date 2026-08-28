from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import fitz
import pytesseract
from pdf2image import convert_from_bytes
import cv2
import numpy as np
from PIL import Image
import io

app = FastAPI(title="PDF OCR API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def preprocess_image(pil_img: Image.Image) -> Image.Image:
    open_cv_image = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    processed = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    return Image.fromarray(processed)

@app.get("/")
def health_check():
    return {"status": "ok", "service": "PDF OCR Backend"}

@app.post("/api/ocr")
async def process_ocr(file: UploadFile = File(...), lang: str = Form("por")):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são aceitos.")

    pdf_bytes = await file.read()
    
    try:
        images = convert_from_bytes(pdf_bytes, dpi=300)
        pdf_pesquisavel = fitz.open()

        for img in images:
            cleaned_img = preprocess_image(img)
            pdf_page_bytes = pytesseract.image_to_pdf_or_hocr(
                cleaned_img, lang=lang, extension='pdf'
            )
            page_doc = fitz.open("pdf", pdf_page_bytes)
            pdf_pesquisavel.insert_pdf(page_doc)
            page_doc.close()

        output_buffer = io.BytesIO()
        pdf_pesquisavel.save(output_buffer)
        pdf_pesquisavel.close()

        return Response(
            content=output_buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=ocr_{file.filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no OCR: {str(e)}")