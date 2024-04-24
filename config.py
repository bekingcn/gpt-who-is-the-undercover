import os
import logging
import dotenv

LANGUAGE = "en"
DEBUG = False
app_name = "gpt-undercover"
logger = logging.getLogger(app_name)
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.debug("Initialized logger")

def config(
    openai_api_key=None,
    openai_base_url=None,
    streamlit=False):
    if streamlit:
        import streamlit as st
        os.environ['OPENAI_API_KEY'] = st.secrets["OPENAI_API_KEY"]
        if st.secrets["OPENAI_API_BASE"]:
            os.environ['OPENAI_API_BASE'] = st.secrets["OPENAI_API_BASE"]
        if st.secrets["LANGCHAIN_TRACING_V2"]:
            os.environ['LANGCHAIN_TRACING_V2'] = st.secrets["LANGCHAIN_TRACING_V2"]
            os.environ['LANGCHAIN_ENDPOINT'] = st.secrets["LANGCHAIN_ENDPOINT"]
            os.environ['LANGCHAIN_API_KEY'] = st.secrets["LANGCHAIN_API_KEY"]
            os.environ['LANGCHAIN_PROJECT'] = st.secrets["LANGCHAIN_PROJECT"]
    else:
        dotenv.load_dotenv(override=True)
    # override openai api key with user specified key
    if openai_api_key:
        os.environ['OPENAI_API_KEY'] = openai_api_key
    if openai_base_url:
        os.environ['OPENAI_API_BASE'] = openai_base_url