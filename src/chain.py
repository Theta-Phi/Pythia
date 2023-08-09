from langchain.prompts.prompt import PromptTemplate
from langchain.chains import ConversationalRetrievalChain, LLMChain, RetrievalQA, RetrievalQAWithSourcesChain
from langchain.memory import ConversationBufferMemory
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma

template = """Considering the provided chat history and a subsequent question, 
rewrite the follow-up question to be an independent query.
Chat History:\"""
{chat_history}
\"""
Follow Up Input: \"""
{question}
\"""
Standalone question:"""

condense_question_prompt = PromptTemplate.from_template(template)

TEMPLATE = """ 
You're an helpful AI assistant who provides answers to questions using the provided context.
Your name is Docusila the oracle of delphi.
When the user greets you introduce your self and provide a general overview of your abilities.
When asked about your capabilities, provide a general overview of your ability to assist with questions based on the stored documents.
Provide a detailed answer to the question along with sources.
If you don't know the answer, simply state, "I'm sorry, I don't know the answer to your question.". Do not make up an answer
provide the answers in markdown format.

Question: ```{question}```
{context}

Answer:

Sources:
"""

QA_PROMPT = PromptTemplate(template=TEMPLATE, input_variables=["question", "context"])

def get_chain_gpt(chroma_client,collection_name):
    #create convesational memory
    memory = ConversationBufferMemory(
        memory_key='chat_history', 
        return_messages=True
    )

    #initialise the vector store with the OpenAi embeddings
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma(collection_name=collection_name, embedding_function=embeddings,client=chroma_client)

    # create a chain for asking questions from the stored documents
    q_llm = OpenAI(
        temperature=0.1,
        model_name="gpt-3.5-turbo",
        max_tokens=500,
    )

    question_generator = LLMChain(llm=q_llm, prompt=condense_question_prompt)
    # qa_chain = RetrievalQA.from_chain_type(
    # llm=q_llm,
    # retriever=vectorstore.as_retriever(search_type="mmr", search_kwargs={'k': 5, 'fetch_k': 50}),
    # prompt=condense_question_prompt,
    # return_source_documents=True
    # )

    # chain for asking the question based on relevant docs
    llm = ChatOpenAI(
        model_name="gpt-3.5-turbo",
        temperature=0.5,
        max_tokens=500,
    )

    doc_chain = load_qa_chain(llm=llm, chain_type="stuff", prompt=QA_PROMPT)
    # qa_doc_chain = load_qa_chain(llm=llm, chain_type="stuff",prompt=QA_PROMPT)

    # conversational chain
    conversational_chain = ConversationalRetrievalChain(
        retriever=vectorstore.as_retriever(),
        combine_docs_chain=doc_chain,
        question_generator=question_generator,
        memory=memory
    )
    # chain_type_kwargs = {"prompt": QA_PROMPT}
    # conversational_chain = RetrievalQAWithSourcesChain(
    #     llm=llm,
    #     retriever=vectorstore.as_retriever(),
    #     combine_docs_chain=qa_doc_chain,
    #     memory=memory,
    #     return_source_documents=True
    # )

    return conversational_chain