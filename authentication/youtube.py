from langchain.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
from langchain.llms import OpenAI
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
import pinecone
from django.http import StreamingHttpResponse
from langchain.chains.question_answering import load_qa_chain
from django.conf import settings
import os
from django.core.cache import cache
import logging
from . models import PdfDocument,Vectorstore,YouTubeLink
import uuid
from langchain.docstore.document import Document 
from langchain.document_loaders import YoutubeLoader



llm = OpenAI(temperature=0,verbose=True,streaming=True)

pinecone.init(
    api_key="53cbabaf-5606-45f9-993b-5363276c6222",  # find at app.pinecone.io
    environment="us-east-1-aws"  # next to api key in console
)

logger = logging.getLogger(__name__)

CACHE_KEY_PREFIX = "pinecone_index:"

def create_namespace_from_youtube(link,name):
    """
    Creates a namespace in the index for the given file path.
    """
    index_name = "test"

    namespace = name
  
    index_name = embed_doc(link,str(index_name),namespace)
    #Write upsert function. 
    #docsearch = Pinecone.from_documents(texts,embeddings,index_name=index_name) # If it doesn't work use upsert!!!!!!
    #index = pinecone.Index(index_name=index_name)
    return index_name

def embed_doc(link,index_name,namespace):
    embeddings = OpenAIEmbeddings(openai_api_key = "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")
    loader = YoutubeLoader.from_youtube_url(link)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size=100, chunk_overlap=20)
    texts = text_splitter.split_documents(documents)
    print(texts)
    db = Pinecone.from_documents(texts, embeddings,index_name = index_name,namespace=namespace)
    print(db)

    return index_name

def get_index(index):
    cache_key = f"{CACHE_KEY_PREFIX}{index}"
    pinecone_index = cache.get(cache_key)
    if pinecone_index is None:
        try:
            pinecone_index = Vectorstore.objects.get(index=index)
        except Vectorstore.DoesNotExist:
            return None
        
        if not pinecone_index.index:
            pinecone_index.index = index
            pinecone_index.save()

        cache.set(cache_key, pinecone_index)
    return pinecone_index.index

def get_response(query, pinecone_index ,namespace):
    """
    Returns a response to the given query using the given Pinecone index.
    If the Pinecone index is not initialized, it raises a ValueError.
    """
    
    try:
        index = pinecone.Index(index_name=pinecone_index)
        xq = query_pinecone(query)

        xc = index.query(xq,top_k=5, include_metadata=True,namespace=namespace)
        # Use OpenAI API to generate a response
        test2 = []
        for i in xc['matches']:
            metadata = i['metadata']
            text_value = metadata.pop('text', None)
            if text_value is not None:
                test2.append(Document(page_content=text_value,metadata=metadata,lookup_index=0))



        chain = load_qa_chain(llm, chain_type="stuff")
        response = chain.run(input_documents=test2, question=query)
        return response
    
    except AttributeError as e:
        logger.exception(f"Error accessing Pinecone index: {e}")
        return None
    except Exception as e:
        logger.exception(f"Error getting response: {e}")
        return None

def query_pinecone(query):
    # generate embeddings for the query
    embeddings = OpenAIEmbeddings(openai_api_key = "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")
    embed_query = embeddings.embed_query(query)
    # search pinecone index for context passage with the answer
    
    return embed_query

def readYoutube(user, yt_link):
    cache_key = f"pinecone_index_youtube:{user.id}:{yt_link.id}"
    cache_value = cache.get(cache_key)   
    pinecone_index = cache_value.get('index', None) if cache_value else None

    if pinecone_index is None:
        try:
            youtube_link = YouTubeLink.objects.get(user=user,pk=yt_link.id)
        except YouTubeLink.DoesNotExist:
            return None
        pinecone_index, created = Vectorstore.objects.get_or_create(user=user, youtube_link=yt_link, namespace=yt_link.url)

        if created:
            pinecone_index.save()  # Save the object to the database first
            pinecone_index.index = create_namespace_from_youtube(youtube_link.url,youtube_link.url)  # Assign the new UUID value
            pinecone_index.save()

        cache.set(cache_key, {'index': pinecone_index.index, 'namespace': youtube_link.url})

    return pinecone_index.index




