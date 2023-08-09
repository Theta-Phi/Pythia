import os
from datetime import datetime
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import pickle
from pathlib import Path
from htmlTemplates import css, bot_template, user_template
from dotenv import load_dotenv

import chromadb
from chromadb.utils import embedding_functions

from langchain.document_loaders import PyMuPDFLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain

def add_pdfs_to_collection(pdf_docs,text_splitter,chroma_collection):
    # get available documents
    docs_directory = os.path.join("docs")#'./docs'
    available_pdfs = []
    for filename in os.listdir(docs_directory):
        if filename.endswith('.pdf'):
            available_pdfs.append(filename)
    print(available_pdfs)

    for pdf in pdf_docs:
        if pdf.name in available_pdfs:
            st.write(f'{pdf.name} already exists in the store skipping..')
        else:
            with open(os.path.join("docs",pdf.name),"wb") as f: 
                f.write(pdf.getbuffer())
            new_file_path = os.path.join("docs",pdf.name) #f'./docs/{pdf.name}'
            pdf_loader = PyMuPDFLoader(new_file_path)
            pages = pdf_loader.load()
            chroma_docs=[]
            doc_metas = []
            doc_ids = []
            for page in pages:
                creationDate = datetime.strptime(page.metadata["creationDate"][:-7], "D:%Y%m%d%H%M%S")
                modDate = datetime.strptime(page.metadata["modDate"][:-7], "D:%Y%m%d%H%M%S")
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

def handle_question(user_question,chroma_collection,memory):
    bot_image = os.getenv('BOT_IMAGE')
    user_image = os.getenv('USER_IMAGE')
    #get  the embeddings for the user question
    embedding_vector = OpenAIEmbeddings().embed_query(user_question)
    #find the source relevant to the question using query vector
    relevant_docs = chroma_collection.query(
        query_embeddings=embedding_vector,
        n_results=15,
        )

    #create a vector store from relevant documents
    vectorstore = Chroma.from_texts(relevant_docs["documents"][0], OpenAIEmbeddings())
    
    #with the configured vector store and the memory build the conversational chain
    #create chatmodel
    llm = ChatOpenAI(model_name="gpt-3.5-turbo")
    #send the question and source to openai
    convesational_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory
        )
    
    # send the query to the conversational chain
    response = convesational_chain({"question": user_question})
    
    # add the response to the chat history
    st.session_state.chat_history = st.session_state.chat_history + response['chat_history']

    # go over the chat history in the revese order so that the latest message is in at the top
    for i, message in enumerate(reversed(st.session_state.chat_history)):
        if i % 2 == 0:
            st.write(bot_template.replace(
                "{{MSG}}", message.content).replace(
                "{{IMG_SRC}}", bot_image
                ), unsafe_allow_html=True)
            
        else:
            st.write(user_template.replace(
                "{{MSG}}", message.content).replace(
                "{{IMG_SRC}}", user_image
                ), unsafe_allow_html=True)



def main():
    load_dotenv()

    #get env variables
    chroma_address=os.getenv('CHROMA_ADDR')
    chroma_port=os.getenv('CHROMA_PORT')
    openai_key = os.getenv('OPENAI_API_KEY')
    app_name=os.getenv('APP_NAME')
    credentials_filename = os.getenv('CREDENTIALS_FILE')
    collection_name = os.getenv('COLLECTION_NAME')

    #create embeddings function for chromadb
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                api_key=openai_key,
                model_name="text-embedding-ada-002"
            )
    
    #initialise chroma client with presistent store
    chroma_client = chromadb.HttpClient(host=chroma_address, port=chroma_port)

    # check if the chroma collection already exists. If it doesn't - create it with the openai embeddings function
    # creating the collection with the embedding function allow us to add documents directly and let 
    #chroma do the embeddings for us
    chroma_collection = chroma_client.get_collection(
        name=collection_name,
        embedding_function=openai_ef
        )
    
    #create text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 1500,
        chunk_overlap  = 150,
        length_function = len,
    )

    #create convesational memory
    memory = ConversationBufferMemory(
        memory_key='chat_history', 
        return_messages=True
    )

    #initialise session object
    if "conversation" not in st.session_state:
        st.session_state.conversation = None

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # set up streamlit ui
    st.set_page_config(page_title=app_name,page_icon=":books:")
    st.write(css, unsafe_allow_html=True)
    st.header("Delphi")

    # --- USER AUTHENTICATION ---
    credentials_file = os.path.join("static",credentials_filename)
    with open(credentials_file) as file:
        credentials = yaml.load(file, Loader=SafeLoader)
    
    authenticator = stauth.Authenticate(
        credentials['credentials'],
        credentials['cookie']['name'],
        credentials['cookie']['key'],
        credentials['cookie']['expiry_days'],
        credentials['preauthorized']
        )
    
    name, authentication_status, username = authenticator.login('Login', 'main')

    if authentication_status == False:
        st.error("Username/password is incorrect")

    if authentication_status == None:
        st.warning("Please enter your username and password")

    if authentication_status:
        st.write(f'Welcome *{name}*')
        # Text input for user Questions
        st.subheader("Questions:")
        user_question = st.text_input("ask a specific questions or set the context by specifying what topic you would like to talk about")
        if user_question:
            handle_question(user_question,chroma_collection,memory)

        #document loader
        with st.sidebar:
            authenticator.logout('Logout', 'main')  
            # Document upload section
            # st.subheader(f"Available documents: {len(available_docs)}")
            # for i,doc in enumerate(available_docs):
            #     st.write(f'{i} - {doc}')
            
            st.subheader("Upload documents")
            pdf_docs = st.file_uploader(
                "Drag n Drop PDFs here and click on 'Process'",type=['pdf'], accept_multiple_files=True)
            if st.button("Process"):
                with st.spinner("Processing"):
                    if add_pdfs_to_collection(pdf_docs,text_splitter,chroma_collection):
                        print('uploaded docs added to the chroma collection')
                        st.write('document upload complete')


if __name__ == '__main__':
    main()