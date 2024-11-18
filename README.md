# Forum Chat with RAG

A tool for scraping forum threads and creating an intelligent chatbot interface. Downloads forum posts page by page, then uses RAG (Retrieval Augmented Generation) with GPT-4 to enable natural conversations about the forum content.

## Requirements

- Python 3.8+
- Export your OpenAI API key:
    ```
    export OPENAI_API_KEY='your-api-key'
    ```

### Python Packages
- langchain
- langchain-openai 
- langchain-community
- beautifulsoup4
- requests
- gradio
- faiss-cpu
- openai

You can install all required packages via pip:
```
pip install langchain langchain-openai langchain-community beautifulsoup4 requests gradio faiss-cpu openai
```


## Components

- `scrape.py`: Handles the forum scraping functionality, downloading posts and metadata from forum threads and saving them to JSON/TXT formats.

- `demo_page.py`: Creates an interactive chatbot interface using Gradio and LangChain, allowing users to ask questions about the forum content with relevant source posts displayed.