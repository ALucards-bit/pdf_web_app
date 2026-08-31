@app.post("/api/ocr")
async def process_ocr(file: UploadFile = File(...), lang: str = Form("por")):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são aceitos.")

    pdf_bytes = await file.read()
    
    try:
        # 1. Converte o PDF enviado em uma lista de imagens PIL (DPI 150 para economizar RAM)
        images = convert_from_bytes(pdf_bytes, dpi=150)
        
        if not images:
            raise HTTPException(status_code=400, detail="Não foi possível extrair páginas do PDF.")

        # 2. Processa o OCR de todas as páginas de uma vez e gera os bytes do PDF
        pdf_final_bytes = pytesseract.image_to_pdf_or_hocr(images, lang=lang, extension='pdf')

        # 3. Retorna os bytes diretamente
        return Response(
            content=pdf_final_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=ocr_{file.filename}"}
        )
    except Exception as e:
        print(f"Erro no OCR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro no OCR: {str(e)}")
