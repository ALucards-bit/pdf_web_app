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

        # --- CORREÇÃO AQUI ---
        # Salva diretamente em bytes via PyMuPDF (tobytes)
        pdf_final_bytes = pdf_pesquisavel.tobytes()
        pdf_pesquisavel.close()

        return Response(
            content=pdf_final_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=ocr_{file.filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no OCR: {str(e)}")
