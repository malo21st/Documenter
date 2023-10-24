""" env\Scripts\Activate.ps1 """
import streamlit as st
import os
os.environ["OPENAI_API_KEY"] = st.secrets.openai_api_key
from llama_index import LLMPredictor, ServiceContext, StorageContext, load_index_from_storage, QuestionAnswerPrompt
from langchain.chat_models import ChatOpenAI
import fitz  # PyMuPDF

pdf_path = "./static/NOBDATA_ChatGPT活用個別サービス開発資料.pdf"

INTRO = "左側のテキストボックスに質問を入力しエンターキーを押すと、ＡＩが回答します。"

if "qa" not in st.session_state:
    st.session_state["qa"] = {"history": [{"role": "A", "msg": INTRO}]}

if "metadata" not in st.session_state:
    st.session_state["metadata"] = {"file_name": "", "slide_num": 0, "text": "", "score": ""}

# Prompt
QA_PROMPT_TMPL = (
    "以下のスライドの情報が与えられています。\n"
    "---------------------\n"
    "{context_str}"
    "\n---------------------\n"
    "この情報を元に次の質問に日本語で簡潔に答えてください: {query_str}\n"
    "# 関連の低いスライドの情報は無視して下さい\n"
    "# 答えがスライドの情報になければ答えないで下さい\n"
)
QA_PROMPT = QuestionAnswerPrompt(QA_PROMPT_TMPL)

@st.cache_resource
def load_vector_db():
    llm_predictor = LLMPredictor(llm=ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo", streaming=True))
    service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor)
    storage_context = StorageContext.from_defaults(persist_dir="./storage/")
    index = load_index_from_storage(storage_context, service_context=service_context)
    return index

@st.cache_resource
def first_slide():
    pdf_document = fitz.open(pdf_path)
    slide_data = pdf_document.load_page(0)
    image = slide_data.get_pixmap()
    image_data = image.tobytes("png")
    return image_data

def store_del_msg():
    if st.session_state.user_input and st.session_state.qa["history"][-1]["role"] != "Q": # st.session_state.prev_q != st.session_state.user_input:
        st.session_state.qa["history"].append({"role": "Q", "msg": st.session_state.user_input}) # store
    st.session_state.user_input = ""  # del

# View (User Interface)
## Sidebar
st.sidebar.title("Documenter Demo")
user_input = st.sidebar.text_input("質問をどうぞ", key="user_input", on_change=store_del_msg)
st.sidebar.markdown("---")
if st.sidebar.button("ＡＩおしゃべりロボって何ですか"):
    st.session_state.qa["history"].append({"role": "Q", "msg": "ＡＩおしゃべりロボって何ですか"})
if st.sidebar.button("ＡＩおりこうロボって何ですか"):
    st.session_state.qa["history"].append({"role": "Q", "msg": "ＡＩおりこうロボって何ですか"})
if st.sidebar.button("Documenterって何ですか"):
    st.session_state.qa["history"].append({"role": "Q", "msg": "Documenterって何ですか"})
if st.sidebar.button("プロンプトセッターって何ですか"):
    st.session_state.qa["history"].append({"role": "Q", "msg": "プロンプトセッターって何ですか"})
slide_img = first_slide()
st.sidebar.image(slide_img, caption="NOBDATA_ChatGPT活用個別サービス開発資料.pptx", use_column_width="auto")

## Main Content
for message in st.session_state.qa["history"]:
    if message["role"] == "Q": # Q: Question (User)
        st.info(message["msg"])
    elif message["role"] == "A": # A: Answer (AI Assistant)
        st.write(message["msg"])
    elif message["role"] == "E": # E: Error
        st.error(message["msg"])
chat_box = st.empty() # Streaming message
pdf_page = st.container()

# Model (Business Logic)
index = load_vector_db()
engine = index.as_query_engine(text_qa_template=QA_PROMPT, streaming=True, similarity_top_k=2)

if st.session_state.qa["history"][-1]["role"] == "Q":
    query = st.session_state.qa["history"][-1]["msg"]
    try:
        response = engine.query(query) # Query to ChatGPT
        text = ""
        for next in response.response_gen:
            text += next
            chat_box.markdown(text + "▌")
        file_name = response.source_nodes[0].node.metadata["file_name"]
        slide_num = int(response.source_nodes[0].node.metadata["slide_num"])
        text_cntx = response.source_nodes[0].node.text
        score = response.source_nodes[0].score
        refer_pages = f"\n\n#{slide_num}　{file_name}\n\n\n"
        chat_box.write(text + refer_pages)
        st.session_state.qa["history"].append({"role": "A", "msg": text + refer_pages})
        st.session_state.metadata["file_name"] = file_name
        st.session_state.metadata["slide_num"] = slide_num
        st.session_state.metadata["text"] = text_cntx
        st.session_state.metadata["score"] = score
    except Exception as error_msg:
        st.error(error_msg)
        st.session_state.qa["history"].append({"role": "E", "msg": error_msg})

    with pdf_page:
        with st.expander(f"スライド表示"):
            file_name = st.session_state.metadata["file_name"]
            slide_num = st.session_state.metadata["slide_num"]
            text_cntx = st.session_state.metadata["text"]
            pdf_document = fitz.open(pdf_path)
            slide_data = pdf_document.load_page(slide_num)
            image = slide_data.get_pixmap()
            image_data = image.tobytes("png")
            st.image(image_data, caption=f"#{slide_num}　{file_name}", use_column_width="auto")
            st.write(text_cntx)
