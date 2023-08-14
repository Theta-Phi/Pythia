# Introduction

Delphi is a helpful chatbot to assist with quering multiple documents in multiple collections. The AI uses openAI API with langchain. The system requires a ChromaDB server for the vectorstore.

The application uses the streamlit library for the forntend.

Security:

Security is implemented using the streamlit authenticator function

## Deployment

### Update Credentials

Streamlit autheticator requires hashed passwords. To setup authetication update the credentials file (/src/static/credentials_example.yml) with the user information and passwords.

Once you are happy with the credentials run gen_pwd.py with the credentials file path passed in as an argument. This will hash the passwords and in the file. Add the file path to the environment variables.

### Deploy

The fastest way to deploy is to use the packaged docker compose file. Update the following environment variables:

          - OPENAI_API_KEY= <YOUR OPEN API KEY>
          - CHROMA_ADDR= <IP ADDRESS FOR THE CHROMADB SERVER>
          - CHROMA_PORT= <PORT FOR THE CHROMADB SERVER>
          - APP_NAME= <APP NAME>
          - CREDENTIALS_FILE= <PATH TO THE CREDENTIALS FILE>
          - BOT_IMAGE= <PATH FOR THE AVATAR IMAGE TO BE USED NEEDS TO BE WEB ADDRESS>
