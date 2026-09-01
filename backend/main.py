import io
import os
import tempfile
import pytesseract
import pdfplumber
import pandas as pd
from pdf2image import convert_from_bytes
import pymupdf as fitz
from pdf2docx import Converter
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="PDF Studio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "ok", "service": "PDF Studio Backend"}

@app.post("/api/ocr")
async def process_ocr(file: UploadFile = File(...), lang: str = Form("por")):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são aceitos.")

    pdf_bytes = await file.read()
    try:
        images = convert_from_bytes(pdf_bytes, dpi=120)
        if not images:
            raise HTTPException(status_code=400, detail="O PDF está vazio.")
        if len(images) > 10:
            raise HTTPException(status_code=400, detail="Envie um PDF de até 10 páginas.")

        pdf_pesquisavel = fitz.open()
        for img in images:
            pdf_page_bytes = pytesseract.image_to_pdf_or_hocr(img, lang=lang, extension='pdf')
            page_doc = fitz.open("pdf", pdf_page_bytes)
            pdf_pesquisavel.insert_pdf(page_doc)
            page_doc.close()

        output_pdf_bytes = pdf_pesquisavel.tobytes()
        pdf_pesquisavel.close()

        return Response(
            content=output_pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=ocr_{file.filename}"}
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no OCR: {str(e)}")

@app.post("/api/convert/word")
async def convert_to_word(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são aceitos.")

    pdf_bytes = await file.read()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(pdf_bytes)
        temp_pdf_path = temp_pdf.name

    temp_docx_path = temp_pdf_path.replace(".pdf", ".docx")

    try:
        cv = Converter(temp_pdf_path)
        cv.convert(temp_docx_path, start=0, end=None)
        cv.close()

        with open(temp_docx_path, "rb") as docx_file:
            docx_bytes = docx_file.read()

        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={file.filename.replace('.pdf', '')}.docx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na conversão para Word: {str(e)}")
    finally:
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
        if os.path.exists(temp_docx_path):
            os.remove(temp_docx_path)

@app.post("/api/convert/excel")
async def convert_to_excel(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são aceitos.")

    pdf_bytes = await file.read()
    try:
        tables_found = []
        
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                extracted_tables = page.extract_tables()
                for table in extracted_tables:
                    if table:
                        df = pd.DataFrame(table)
                        tables_found.append((f"Página_{page_idx + 1}", df))

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            if tables_found:
                for idx, (sheet_name, df) in enumerate(tables_found):
                    df.to_excel(writer, index=False, header=False, sheet_name=f"Tabela_{idx + 1}")
            else:
                with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                    text_data = []
                    for page_idx, page in enumerate(pdf.pages):
                        text = page.extract_text() or ""
                        for line in text.split("\n"):
                            if line.strip():
                                text_data.append({"Página": page_idx + 1, "Conteúdo": line.strip()})
                    df_fallback = pd.DataFrame(text_data)
                    df_fallback.to_excel(writer, index=False, sheet_name="Texto Extraído")

        buffer.seek(0)

        return Response(
            content=buffer.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={file.filename.replace('.pdf', '')}.xlsx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao converter para Excel: {str(e)}")
