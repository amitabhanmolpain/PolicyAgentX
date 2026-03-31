from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

splitter = RecursiveCharacterTextSplitter(
    chunk_size=600,       # sweet spot for policy text
    chunk_overlap=80,     # overlap so context isn't lost at edges
    separators=["\n\n", "\n", "|", " "]
)

def make_documents(texts: list[str], source: str) -> list[Document]:
    docs = []
    for text in texts:
        chunks = splitter.split_text(text)
        for chunk in chunks:
            docs.append(Document(
                page_content=chunk,
                metadata={"source": source}
            ))
    return docs