import os
from datetime import datetime
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyMuPDFLoader
import streamlit as st

# functions for ingesting differrent doc types and storing them in the chorma db with metadatas

def add_pdf_to_collection(pdf,text_splitter,chroma_collection,docs_folder):
    #Copy the incoming file to the local storage folder
    with open(os.path.join(docs_folder,pdf.name),"wb") as f:
        f.write(pdf.getbuffer())

    new_file_path = os.path.join(docs_folder,pdf.name) #f'./docs/{collection_name}/{pdf.name}'
    pdf_loader = PyMuPDFLoader(new_file_path)
    pages = pdf_loader.load()
    chroma_docs=[]
    doc_metas = []
    doc_ids = []
    for page in pages:
        try:
            creationDate = datetime.strptime(page.metadata["creationDate"][:-7], "D:%Y%m%d%H%M%S")
        except:
            creationDate = datetime.strptime("20230908000000", "D:%Y%m%d%H%M%S")
        try:
            modDate = datetime.strptime(page.metadata["modDate"][:-7], "D:%Y%m%d%H%M%S")
        except:
            modDate = datetime.strptime("20230908000000", "D:%Y%m%d%H%M%S")
        #create chunks from each page
        chunks = text_splitter.create_documents([page.page_content])
        # write the chunk to the chroma collection with the meta data from the page and chunk
        for idx,chunk in enumerate(chunks):
            chunk.metadata={
                'source':pdf.name,
                'page':page.metadata["page"],
                'creationDate':creationDate.strftime("%d-%m-%Y %H:%M:%S"),
                'modDate':modDate.strftime("%d-%m-%Y %H:%M:%S"),
                'author':page.metadata["author"],
                'title':page.metadata["title"],
            }
            chunk_id = chunk.metadata['source']+'_'+str(chunk.metadata['page'])+'_'+str(idx)
            chroma_docs.append(chunk.page_content)
            doc_metas.append(chunk.metadata)
            doc_ids.append(chunk_id)
    try:
        chroma_collection.upsert(
            documents=chroma_docs,
            metadatas=doc_metas,
            ids=doc_ids
        )
        return True
    except Exception as e:
        print(f'failed to upsert records to the collection exception raised:{e}')
        return False
    
# TODO - Implement a common function for identifying different doc types and call the appropriate ingest function
def ingest_docs(uploaded_docs,chroma_client,collection_name,embedding_func):

    #create text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 1000,
        chunk_overlap  = 150,
        length_function = len,
    )

    # get list available documnents
    docs_directory = os.path.join("docs",st.session_state.collectionName)#'./docs'
    if not os.path.exists(docs_directory): os.makedirs(docs_directory)
    availablae_docs = []
    for filename in os.listdir(docs_directory):
        availablae_docs.append(filename)
    
    # get the collection to upload to
    try:
        chroma_collection = chroma_client.get_collection(collection_name,embedding_func)
        print(chroma_collection.get())
    except:
        st.write("Error while uploading documentation - check the selected collection")
        return False
    
    # iterate over the uploaded documents and upload new ones only
    for doc in uploaded_docs:
        if doc.name in availablae_docs:
            print(f'{doc.name} already exists in the store skipping..')
        else:
            if doc.name.endswith('.pdf') and add_pdf_to_collection(doc,text_splitter,chroma_collection,docs_directory):
                print(f'{doc.name} uploaded to the collection')
            else:
                return False
    return True