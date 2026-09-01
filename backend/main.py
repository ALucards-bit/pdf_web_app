import os
import tempfile
from pdf2docx import Converter
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import Response

# ... (Mantenha as demais configurações e rotas do app) ...

@app.post("/api/convert/word")
async def convert_to_word(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são aceitos.")

    pdf_bytes = await file.read()
    
    # Cria arquivos temporários seguros em disco para o pdf2docx processar
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(pdf_bytes)
        temp_pdf_path = temp_pdf.name

    temp_docx_path = temp_pdf_path.replace(".pdf", ".docx")

    try:
        # Instancia o conversor de PDF para Word reconstruindo a estrutura visual
        cv = Converter(temp_pdf_path)
        cv.convert(temp_docx_path, start=0, end=None)
        cv.close()

        # Lê os bytes do Word gerado
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
        # Garante a limpeza dos arquivos temporários no servidor
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
        if os.path.exists(temp_docx_path):
            os.remove(temp_docx_path)
