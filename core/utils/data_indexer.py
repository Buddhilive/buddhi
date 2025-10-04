from llama_index.readers.file import PDFReader
from llama_index.core.node_parser import SentenceSplitter

def load_and_chunk_pdf(file_path: str):
    loader = PDFReader()
    document = loader.load_data(file=file_path)
    texts = [doc.text for doc in document if getattr(doc, 'text', None)]
    chunks = []
    for text in texts:
        chunks.extend(SentenceSplitter(chunk_size=1024, chunk_overlap=200).split_text(text))
    return chunks