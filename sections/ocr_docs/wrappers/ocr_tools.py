"""Section 7: OCR & Documents — All 20 tools."""
import asyncio, time, json, os, tempfile
from sections.base import BaseTool, ToolResult, ToolCategory

class DoclingOCR(BaseTool):
    name = "docling"; category = ToolCategory.OCR
    capabilities = ["document_parsing", "table_extraction", "layout", "pdf", "docx"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            from docling.document_converter import DocumentConverter
            converter=DocumentConverter()
            result=converter.convert(query if query.startswith("http") else kw.get("file_path",""))
            return ToolResult(source=query,raw=str(result.document),tool=self.name,duration_ms=self._timing(s))
        except ImportError: return ToolResult(source=query,status="error",error="pip install docling",tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class MarkerOCR(BaseTool):
    name = "marker"; category = ToolCategory.OCR
    capabilities = ["pdf_to_markdown", "layout_detection", "ocr", "table"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            from marker.converters.pdf import PdfConverter
            converter=PdfConverter()
            result=converter(kw.get("file_path",""))
            return ToolResult(source=query,raw=str(result),tool=self.name,duration_ms=self._timing(s))
        except ImportError: return ToolResult(source=query,status="error",error="pip install marker-pdf",tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class OCRmyPDFOCR(BaseTool):
    name = "ocrmypdf"; category = ToolCategory.OCR
    capabilities = ["pdf_ocr", "searchable_pdf", "lossless"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import subprocess
            input_file=kw.get("file_path","")
            output_file=kw.get("output_path",tempfile.mktemp(suffix=".pdf"))
            result=subprocess.run(["ocrmypdf","--force-ocr",input_file,output_file],capture_output=True,text=True)
            return ToolResult(source=query,raw=result.stdout+result.stderr,tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class TesseractOCR(BaseTool):
    name = "tesseract"; category = ToolCategory.OCR
    capabilities = ["ocr", "multi_lang", "hindi", "eng", "tesseract4"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            from PIL import Image
            import pytesseract
            img=Image.open(kw.get("file_path",query))
            text=pytesseract.image_to_string(img,lang=kw.get("lang","eng+hin"))
            return ToolResult(source=query,raw=text,tool=self.name,duration_ms=self._timing(s))
        except ImportError: return ToolResult(source=query,status="error",error="pip install pytesseract Pillow",tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class PaddleOCROCR(BaseTool):
    name = "paddleocr"; category = ToolCategory.OCR
    capabilities = ["ocr", "layout_detection", "table_rec", "chinese", "hindi", "multi_lang"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            from paddleocr import PaddleOCR
            ocr=PaddleOCR(lang=kw.get("lang","en"))
            result=ocr.ocr(kw.get("file_path",query))
            texts=[line[1][0] for line in result[0]] if result and result[0] else []
            return ToolResult(source=query,raw="\n".join(texts),tool=self.name,duration_ms=self._timing(s))
        except ImportError: return ToolResult(source=query,status="error",error="pip install paddlepaddle paddleocr",tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class EasyOCR(BaseTool):
    name = "easyocr"; category = ToolCategory.OCR
    capabilities = ["ocr", "multi_lang", "hindi", "80+ languages"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import easyocr
            reader=easyocr.Reader(kw.get("languages",["en","hi"]))
            result=reader.readtext(kw.get("file_path",query))
            texts=[r[1] for r in result]
            return ToolResult(source=query,raw="\n".join(texts),tool=self.name,duration_ms=self._timing(s))
        except ImportError: return ToolResult(source=query,status="error",error="pip install easyocr",tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class SuryaOCR(BaseTool):
    name = "surya"; category = ToolCategory.OCR
    capabilities = ["ocr", "layout_detection", "line_detection", "table_rec", "multi_lang"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            from surya.ocr import run_ocr
            from surya.model.detection.model import load_model as load_det_model
            from surya.model.recognition.model import load_model as load_rec_model
            det_model=load_det_model()
            rec_model=load_rec_model()
            images=[kw.get("file_path",query)]
            results=run_ocr(images,[[kw.get("lang","English")]],det_model,rec_model)
            texts=[line.text for r in results for line in r.text_lines]
            return ToolResult(source=query,raw="\n".join(texts),tool=self.name,duration_ms=self._timing(s))
        except ImportError: return ToolResult(source=query,status="error",error="pip install surya-ocr",tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class NougatOCR(BaseTool):
    name = "nougat"; category = ToolCategory.OCR
    capabilities = ["scientific_pdf", "equations", "tables", "markdown"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=120) as c:
                r=await c.post("http://localhost:8092/predict",json={"file":kw.get("file_path",query)})
                return ToolResult(source=query,raw=r.text[:10000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class PyMuPDFTool(BaseTool):
    name = "pymupdf"; category = ToolCategory.OCR
    capabilities = ["pdf_read", "text_extract", "images", "metadata", "search"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import pymupdf
            doc=pymupdf.open(kw.get("file_path",query))
            text="\n".join([page.get_text() for page in doc])
            return ToolResult(source=query,raw=text[:10000],metadata={"pages":len(doc)},tool=self.name,duration_ms=self._timing(s))
        except ImportError: return ToolResult(source=query,status="error",error="pip install pymupdf",tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class PdfPlumberTool(BaseTool):
    name = "pdfplumber"; category = ToolCategory.OCR
    capabilities = ["pdf_read", "table_extract", "text", "metadata"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import pdfplumber
            with pdfplumber.open(kw.get("file_path",query)) as pdf:
                text="\n".join([page.extract_text() or "" for page in pdf.pages])
                tables=[page.extract_tables() for page in pdf.pages]
            return ToolResult(source=query,raw=text[:10000],metadata={"tables_found":len(tables)},tool=self.name,duration_ms=self._timing(s))
        except ImportError: return ToolResult(source=query,status="error",error="pip install pdfplumber",tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class CamelotTool(BaseTool):
    name = "camelot"; category = ToolCategory.OCR
    capabilities = ["pdf_tables", "lattice", "stream", "export"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import camelot
            tables=camelot.read_pdf(kw.get("file_path",query),pages=kw.get("pages","all"))
            data=[t.df.to_dict() for t in tables]
            return ToolResult(source=query,raw=json.dumps(data),metadata={"table_count":len(tables)},tool=self.name,duration_ms=self._timing(s))
        except ImportError: return ToolResult(source=query,status="error",error="pip install camelot-py[cv]",tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class TabulaTool(BaseTool):
    name = "tabula"; category = ToolCategory.OCR
    capabilities = ["pdf_tables", "java_based", "multiple_pages"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import tabula
            dfs=tabula.read_pdf(kw.get("file_path",query),pages=kw.get("pages","all"))
            data=[df.to_dict() for df in dfs]
            return ToolResult(source=query,raw=json.dumps(data),metadata={"table_count":len(dfs)},tool=self.name,duration_ms=self._timing(s))
        except ImportError: return ToolResult(source=query,status="error",error="pip install tabula-py",tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class UnstructuredTool(BaseTool):
    name = "unstructured"; category = ToolCategory.OCR
    capabilities = ["document_parsing", "chunking", "partition", "pdf", "docx", "html"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            from unstructured.partition.auto import partition
            elements=partition(filename=kw.get("file_path",query))
            text="\n".join([str(e) for e in elements])
            return ToolResult(source=query,raw=text[:10000],metadata={"element_count":len(elements)},tool=self.name,duration_ms=self._timing(s))
        except ImportError: return ToolResult(source=query,status="error",error="pip install unstructured",tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class ApacheTikaTool(BaseTool):
    name = "tika"; category = ToolCategory.OCR
    capabilities = ["content_extraction", "metadata", "multi_format", "detection"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            from tika import parser
            parsed=parser.from_file(kw.get("file_path",query))
            return ToolResult(source=query,raw=parsed.get("content","")[:10000],metadata=parsed.get("metadata",{}),tool=self.name,duration_ms=self._timing(s))
        except ImportError: return ToolResult(source=query,status="error",error="pip install tika",tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class GROBIDTool(BaseTool):
    name = "grobid"; category = ToolCategory.OCR; requires_docker = True
    capabilities = ["scholarly_pdf", "TEI_xml", "references", "metadata", "citations"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=120) as c:
                with open(kw.get("file_path",query),"rb") as f:
                    r=await c.post("http://localhost:8070/api/processFulltextDocument",files={"input":f})
                return ToolResult(source=query,raw=r.text[:10000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class PyMuPDF4LLMTool(BaseTool):
    name = "pymupdf4llm"; category = ToolCategory.OCR
    capabilities = ["pdf_to_markdown", "llm_ready", "tables", "images"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import pymupdf4llm
            md_text=pymupdf4llm.to_markdown(kw.get("file_path",query))
            return ToolResult(source=query,raw=md_text[:10000],tool=self.name,duration_ms=self._timing(s))
        except ImportError: return ToolResult(source=query,status="error",error="pip install pymupdf4llm",tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class LayoutParserTool(BaseTool):
    name = "layoutparser"; category = ToolCategory.OCR
    capabilities = ["layout_detection", "OCR", "table", "document_layout"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=60) as c:
                r=await c.post("http://localhost:8093/parse",json={"file":kw.get("file_path",query)})
                return ToolResult(source=query,raw=r.text[:10000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class MarkerPDFTool(BaseTool):
    name = "marker_pdf"; category = ToolCategory.OCR
    capabilities = ["pdf_to_markdown", "batch", "ocr", "layout"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=120) as c:
                r=await c.post("http://localhost:8094/convert",json={"file":kw.get("file_path",query)})
                return ToolResult(source=query,raw=r.text[:10000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class MinerUTool(BaseTool):
    name = "mineru"; category = ToolCategory.OCR
    capabilities = ["pdf_parsing", "layout", "ocr", "markdown", "table"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=120) as c:
                r=await c.post("http://localhost:8095/parse",json={"file":kw.get("file_path",query),"method":"auto"})
                return ToolResult(source=query,raw=r.text[:10000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class PopplerTool(BaseTool):
    name = "poppler"; category = ToolCategory.OCR
    capabilities = ["pdf_utils", "pdftotext", "pdfinfo", "pdftoppm", "cli"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import subprocess
            result=subprocess.run(["pdftotext",kw.get("file_path",query),"-"],capture_output=True,text=True)
            return ToolResult(source=query,raw=result.stdout[:10000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

OCR_REGISTRY = {
    "docling": DoclingOCR, "marker": MarkerOCR, "ocrmypdf": OCRmyPDFOCR,
    "tesseract": TesseractOCR, "paddleocr": PaddleOCROCR, "easyocr": EasyOCR,
    "surya": SuryaOCR, "nougat": NougatOCR, "pymupdf": PyMuPDFTool,
    "pdfplumber": PdfPlumberTool, "camelot": CamelotTool, "tabula": TabulaTool,
    "unstructured": UnstructuredTool, "tika": ApacheTikaTool, "grobid": GROBIDTool,
    "pymupdf4llm": PyMuPDF4LLMTool, "layoutparser": LayoutParserTool,
    "marker_pdf": MarkerPDFTool, "mineru": MinerUTool, "poppler": PopplerTool,
}
