from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from typing import List
import tempfile
from pathlib import Path
import time

from deepdoc.parser import (
    PdfParser, DocxParser, ExcelParser, PptParser,
    HtmlParser, JsonParser, MarkdownParser, TxtParser
)

app = FastAPI(
    title="Document Parser API",
    description="API for parsing various document formats",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 文件类型到解析器的映射
PARSER_MAP = {
    ".pdf": PdfParser,
    ".docx": DocxParser,
    ".xlsx": ExcelParser,
    ".xls": ExcelParser,
    ".pptx": PptParser,
    ".ppt": PptParser,
    ".html": HtmlParser,
    ".json": JsonParser,
    ".md": MarkdownParser,
    ".txt": TxtParser,
}

@app.post("/parse")
async def parse_document(file: UploadFile = File(...)):
    """
    上传并解析文档
    
    参数:
    - file: 要解析的文件
    
    返回:
    - 解析后的文档内容
    """
    temp_file = None
    try:
        # 获取文件后缀
        suffix = Path(file.filename).suffix.lower()
        
        # 检查文件类型是否支持
        if suffix not in PARSER_MAP:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {suffix}. Supported types are: {', '.join(PARSER_MAP.keys())}"
            )
        
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        try:
            # 写入上传的文件内容
            content = await file.read()
            temp_file.write(content)
            temp_file.flush()
            temp_file.close()  # 显式关闭文件
            
            # 获取对应的解析器
            parser = PARSER_MAP[suffix]()
            # 解析文档
            result = parser(temp_file.name)
            return {"status": "success", "content": result}
        finally:
            if temp_file:
                try:
                    # 尝试删除文件，如果失败则等待一段时间后重试
                    max_retries = 3
                    for i in range(max_retries):
                        try:
                            if os.path.exists(temp_file.name):
                                os.unlink(temp_file.name)
                            break
                        except PermissionError:
                            if i < max_retries - 1:
                                time.sleep(0.1)  # 等待100ms后重试
                            else:
                                print(f"Warning: Could not delete temporary file: {temp_file.name}")
                except Exception as e:
                    print(f"Warning: Error while deleting temporary file: {str(e)}")
                
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )

@app.get("/supported-formats")
async def get_supported_formats():
    """获取支持的文件格式列表"""
    return {"supported_formats": list(PARSER_MAP.keys())}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True) 