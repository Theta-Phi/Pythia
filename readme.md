# Introduction

Pythia is a helpful chatbot to assist with quering multiple documents in multiple collections. The AI uses openAI API with langchain. The system requires a ChromaDB server for the vectorstore.

The application uses the streamlit library for the forntend.

Security is implemented using the streamlit authenticator function

## Deployment

### Update Credentials

Streamlit autheticator requires hashed passwords. To setup authetication update the credentials file (/src/static/credentials_example.yml) with the user information and passwords and rename the file to credentials.yml.

The passwords are hashed as part of the image build process so readable passwords are not available with the deployed application.

### Deploy

The fastest way to deploy is to use the packaged docker compose file. Enter you API Key for OpenAI in the environment variables:

          - OPENAI_API_KEY= <YOUR OPEN API KEY>

### Under the hood

Each collection is mapped to a local directory so all files uploaded are stored on the server. When a file gets uploaded the meta data is extracted/augumented, tokenized and saved to the vector store (Chroma DB) - this uses openAI embeddings.

On a new query - the query is vectorized (using openAI embeddings) and used to find relevant documents in the vector store. The vectorized relevant documents alongwith the vectorized query is sent to openAI as a prompt to get a contextualized answer back.

What is logged:
- Login
- when new documents are uploaded
- Collection creation / deletion
- start/reset of a new converstaion chain

What is not logged:
- chat / queries
- chat history
- details of individual documents uploaded
- general interaction
