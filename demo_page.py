import os
import json
import textwrap
import gradio as gr
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain

from typing import Dict, List

class ForumChatbot:
    def __init__(self, json_file: str):
        self.raw_data = self.load_json(json_file)
        self.posts_by_id = {post['post_number']: post for post in self.raw_data['posts']}
        self.setup_chain()
        
    def load_json(self, json_file: str) -> Dict:
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def setup_chain(self):
        # Prepare documents
        documents = []
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        # Create documents with metadata
        for post in self.raw_data['posts']:
            text = f"{post['content']}"
            chunks = text_splitter.create_documents(
                [text],
                metadatas=[{
                    'post_number': post['post_number'],
                    'username': post['username'],
                    'date': post['date']
                }] * len(text_splitter.split_text(text))
            )
            documents.extend(chunks)
        
        # Create vector store
        embeddings = OpenAIEmbeddings()
        self.vectorstore = FAISS.from_documents(documents, embeddings)
        
        # Create chat chain
        llm = ChatOpenAI(temperature=0.7, model='gpt-4o')
        self.chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 3}),
            return_source_documents=True,
            verbose=True
        )
    
    def format_source_post(self, post_number: str) -> str:
        post = self.posts_by_id[post_number]
        return f"""
<div style='background-color: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; border: 1px solid #e0e0e0;'>
    <div style='color: #2d3748; margin-bottom: 10px; font-family: system-ui, -apple-system, sans-serif;'>
        <strong style='color: #1a202c;'>Post #{post['post_number']}</strong> 
        by <em style='color: #4a5568;'>{post['username']}</em>
        <br>
    </div>
    <div style='color: #1a202c; white-space: pre-wrap; font-family: system-ui, -apple-system, sans-serif;'>
        {textwrap.fill(post['content'], width=80)}
    </div>
</div>

"""
    
    def get_answer(self, question: str, history: List) -> tuple:
        # Convert history to the format expected by the chain
        chat_history = [(q, a) for q, a in history]
        
        # Get response from the chain
        response = self.chain({"question": question, "chat_history": chat_history})
        
        # Format source posts directly from the documents
        sources_html = "<h3>Source Posts:</h3>"
        seen_content = set()  # To avoid duplicate content
        
        for doc in response['source_documents']:
            # Only show unique content
            if doc.page_content not in seen_content:
                seen_content.add(doc.page_content)
                sources_html += f"""
                <div style='background-color: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; border: 1px solid #e0e0e0;'>
                    <div style='color: #2d3748; margin-bottom: 10px; font-family: system-ui, -apple-system, sans-serif;'>
                        <strong style='color: #1a202c;'>Source</strong> 
                        by <em style='color: #4a5568;'>{doc.metadata.get('username', 'Unknown')}</em>
                    </div>
                    <div style='color: #1a202c; white-space: pre-wrap; font-family: system-ui, -apple-system, sans-serif;'>
                        {textwrap.fill(doc.page_content, width=80)}
                    </div>
                </div>
                """
        
        if not seen_content:
            sources_html += "<p>No relevant sources found.</p>"
        return response['answer'], sources_html

def create_interface(json_file: str):
    chatbot = ForumChatbot(json_file)
    
    with gr.Blocks(css="""
        .source-container { max-height: 600px; overflow-y: auto; }
        .container { margin: 15px; }
        
        /* Style user messages */
        .user-message {
            background-color: #2563eb !important;
            color: white !important;
        }
        
        /* Style assistant messages */
        .assistant-message {
            background-color: #f3f4f6 !important;
            color: black !important;
            border: 1px solid #e5e7eb !important;
        }
        
        /* Add some spacing between messages */
        .message-wrap {
            margin: 8px 0 !important;
        }
        
        /* Style the timestamps */
        .message-timestamp {
            color: #6b7280 !important;
            font-size: 0.8em !important;
        }
    """) as interface:
        gr.Markdown("# S.E.H Kelly Forum Chat")
        gr.Markdown("Ask questions about the forum thread and see source posts!")
        
        with gr.Row():
            with gr.Column(scale=2):
                chatbot_interface = gr.Chatbot(height=600)
                with gr.Row():
                    msg = gr.Textbox(
                        show_label=False,
                        placeholder="Enter your question...",
                        container=False
                    )
                    submit = gr.Button("Send")
            
            with gr.Column(scale=1):
                sources_display = gr.HTML(
                    label="Source Posts",
                    value="Source posts will appear here...",
                    elem_classes=["source-container"]
                )
        
            def respond(message, history):
                answer, sources = chatbot.get_answer(message, history)
                history.append((message, answer))  # Add the new message pair to history
                return history, sources  # Return updated history instead of just the answer

            # And make sure the event listeners are set up correctly
            msg.submit(respond, [msg, chatbot_interface], [chatbot_interface, sources_display], show_progress=True)
            submit.click(respond, [msg, chatbot_interface], [chatbot_interface, sources_display], show_progress=True)
    return interface

if __name__ == "__main__":
    
    # Create and launch the interface
    demo = create_interface("forum_data.json")
    demo.launch(share=True)