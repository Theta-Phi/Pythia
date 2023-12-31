import os, shutil
from datetime import datetime
import streamlit as st
import streamlit_authenticator as stauth
from langchain.chat_models import ChatOpenAI
import yaml
from yaml.loader import SafeLoader
from htmlTemplates import css, bot_template, user_template
from dotenv import load_dotenv
import tiktoken

from ingest import ingest_docs
from chain import get_chain_gpt

import chromadb
from chromadb.utils import embedding_functions

from logger import logger

def num_tokens_from_messages(messages, model="gpt-3.5-turbo"):
    """Return the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    tokens_per_message = 3
    tokens_per_name = 1
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for value in message.content:
            num_tokens += len(encoding.encode(value))
            # if key == "name":
            #     num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens


def reset_chat(chroma_client):
    st.session_state.available_collections = []
    update_chroma_collections(chroma_client)
    st.session_state.collectionName = ''
    st.session_state.conversation=None
    st.session_state.chat_history = []
    logger.info(f'chat reset')


def update_chroma_collections(chroma_client:chromadb.HttpClient):
    chroma_collections = chroma_client.list_collections()
    available_collections=['']
    for collection in chroma_collections:
        available_collections.append(collection.name)
    st.session_state.available_collections = available_collections
    logger.info(f'Chroma collection updated')
    return available_collections

def delete_collection(chroma_client,collectionName):
    try:
        collection_doc_dir = os.path.join('docs',collectionName)
        chroma_client.delete_collection(collectionName)
        logger.info(f'Chroma Collection : {collectionName} deleted by user: {st.session_state.username}')
        # deleted the stored documents:
        if os.path.exists(collection_doc_dir):
            shutil.rmtree(collection_doc_dir)
            logger.info(f'Document Collection at : {collection_doc_dir} deleted by user: {st.session_state.username}')
        return True
    except Exception as e:
        logger.error(f'error while trying to deleted collection {collectionName} Exception: {e}')
        return False


def handle_question(user_question):
    bot_image = os.getenv('BOT_IMAGE')
    convesational_chain = st.session_state.conversation
    chat_history = st.session_state.chat_history
    tokens = num_tokens_from_messages(chat_history)
    while tokens > 3500:
        chat_history.pop(0)
        tokens = num_tokens_from_messages(chat_history)
    # send the query to the conversational chain
    response = convesational_chain({"question": user_question,"chat_history": chat_history})
    
    # update the chat history
    st.session_state.chat_history = response['chat_history']

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
                "{{IMG_SRC}}", st.session_state.user_avater
                ), unsafe_allow_html=True)
            
def load_chain(chroma_client):
    with st.sidebar:
        with st.spinner("loading chain.."):
            st.session_state.conversation = get_chain_gpt(chroma_client=chroma_client,collection_name=st.session_state.collectionName)
            logger.info(f'new conversation chain with chroma collection {st.session_state.collectionName} started by {st.session_state.username}')

def main():
    load_dotenv()

    #get env variables
    chroma_address=os.getenv('CHROMA_ADDR')
    chroma_port=os.getenv('CHROMA_PORT')
    openai_key = os.getenv('OPENAI_API_KEY')
    app_name=os.getenv('APP_NAME')
    credentials_filename = 'credentials.yml'

    # #create embeddings function for chromadb
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                api_key=openai_key,
                model_name="text-embedding-ada-002"
            )
    
    #initialise chroma client with presistent store and get the available collections
    try:
        chroma_client = chromadb.HttpClient(host=chroma_address, port=chroma_port)
    except Exception as e:
        logger.error(f'error: failed to initialise chromadb client {e}')

    #initialise session object
    if "conversation" not in st.session_state:
        st.session_state.conversation = None

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "collectionName" not in st.session_state:
        st.session_state.collectionName = ''
    
    if 'available_collection' not in st.session_state:
        st.session_state.available_collections = []
    
    if 'collection' not in st.session_state:
        st.session_state.collection=None

    # set up streamlit ui
    st.set_page_config(page_title=app_name,page_icon=":books:")
    st.write(css, unsafe_allow_html=True)
    st.header(app_name)

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
        st.session_state.username = username
        st.session_state.user_avater = "https://e7.pngegg.com/pngimages/799/987/png-clipart-computer-icons-avatar-icon-design-avatar-heroes-computer-wallpaper-thumbnail.png"
        logger.info(f'new log in: {st.session_state.username}')
        
        if st.session_state.collectionName != ''and st.session_state.conversation is not None:
            # Text input for user Questions
            st.subheader(f"Active Collection: {st.session_state.collectionName}")
            user_question = st.text_input("ask a specific questions or set the context by specifying what topic you would like to talk about:",value="")
            if user_question:
                handle_question(user_question)
        else:
            st.write("Select a collection from the sidebar and click start..")

        #SideBar
        with st.sidebar:
            #Logout
            authenticator.logout('Logout', 'main')

            # Create a new collection form
            with st.expander("Create a new collection", expanded=False):
                with st.form("my_form",clear_on_submit=True):                    
                    new_collection_name = st.text_input("Name for the new collection",key="new_collection_name")
                    submitted = st.form_submit_button("Create")
                    if submitted:
                        collection_metas = {
                                'created_by' : username,
                                'created_date' : datetime.strftime(datetime.now(),"%d-%m-%Y %H:%M:%S")
                                }
                        chroma_client.get_or_create_collection(name=new_collection_name,
                                                               embedding_function=openai_ef,
                                                               metadata=collection_metas
                                                               )
                        logger.info(f'new collection created by {st.session_state.username} - collection: {new_collection_name}')
                        st.session_state.available_collections = []
                        update_chroma_collections(chroma_client)

            #Select an existing collection##
            update_chroma_collections(chroma_client) #updates the collections in st.session_state.available_collections
            st.session_state.collectionName = st.sidebar.selectbox("Select the collection:",options=st.session_state.available_collections)
            if st.session_state.collectionName: 
                st.session_state.collection = chroma_client.get_collection(name=st.session_state.collectionName)
                if st.session_state.collection.metadata == None or "created_by" not in st.session_state.collection.metadata.keys(): 
                    st.session_state.collection.metadata = {'created_by' : 'admin'}

            # Show the selected collection meta in a expander
            if st.session_state.collection is not None:
                with st.expander('Collection Meta',expanded=False):
                    collection_created_by = st.session_state.collection.metadata['created_by']
                    collection_created_date = st.session_state.collection.metadata['created_date']
                    st.write(f'created by: {collection_created_by}')
                    st.write(f'Date created: {collection_created_date}')


            # Build the conversation chain model and set the collection
            st.button("Start", on_click=load_chain,args=(chroma_client,))

            # Reset the conversation chain and other session elements    
            st.button("Reset Chat",on_click=reset_chat,args=(chroma_client,))
            
            # check if the collection can be deleted by the user and enable the delete button
            if st.session_state.collection is not None:
                if st.session_state.collection.metadata['created_by'] == username or username == 'admin':
                    if st.button("Delete Collection"):
                        with st.spinner("deleting.."):
                            if delete_collection(chroma_client,st.session_state.collectionName):
                                reset_chat(chroma_client)
                                st.write(f'collection deleted')
                            else:
                                st.write(f'Error while trying to delete collection')
            
            # Upload documents
            if st.session_state.collectionName != '' and st.session_state.conversation is not None:
                with st.expander("upload docs", expanded=False):
                    uploaded_docs = st.file_uploader(
                        "Drag n Drop PDFs here and click on 'Process'",type=['pdf'], accept_multiple_files=True)
                    if st.button("Process"):
                        with st.spinner("Processing"):
                            if ingest_docs(uploaded_docs,chroma_client,st.session_state.collectionName,openai_ef):
                                st.session_state.collection = chroma_client.get_collection(st.session_state.collectionName,openai_ef)
                                st.write(f'document upload complete..')
                                logger.info(f'new documents uploaded by {st.session_state.username} in collection {st.session_state.collectionName}')
                            else:
                                st.write(f'Error while uploading docs')
                                logger.error(f'error while uploading new documents to the {st.session_state.collectionName}')

if __name__ == '__main__':
    main()