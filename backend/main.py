import io
import docx
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import pytesseract
from pdf2image import convert_from_bytes

# --- Mantenha sua inicialização do app e CORS aqui ---

@app.post("/api/convert/word")
async def convert_to_word(file: UploadFile = File(...), lang: str = Form("por")):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são aceitos.")

    pdf_bytes = await file.read()
    try:
        images = convert_from_bytes(pdf_bytes, dpi=120)
        doc = docx.Document()
        
        for index, img in enumerate(images):
            # Extrai texto de cada página via OCR
            text = pytesseract.image_to_string(img, lang=lang)
            doc.add_heading(f"Página {index + 1}", level=2)
            doc.add_paragraph(text)

        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        return Response(
            content=buffer.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename=convertido_{file.filename}.docx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na conversão para Word: {str(e)}")


@app.post("/api/convert/excel")
async def convert_to_excel(file: UploadFile = File(...), lang: str = Form("por")):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são aceitos.")

    pdf_bytes = await file.read()
    try:
        images = convert_from_bytes(pdf_bytes, dpi=120)
        data = []

        for index, img in enumerate(images):
            # Extrai o texto organizando linhas/parágrafos
            text = pytesseract.image_to_string(img, lang=lang)
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            for line in lines:
                data.append({"Página": index + 1, "Conteúdo": line})

        # Cria uma planilha com os dados extraídos
        df = pd.DataFrame(data)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="Texto Extraído")

        buffer.seek(0)

        return Response(
            content=buffer.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=convertido_{file.filename}.xlsx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na conversão para Excel: {str(e)}")
