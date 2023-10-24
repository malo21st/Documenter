""" env\Scripts\Activate.ps1 """
import streamlit as st
import os
os.environ["OPENAI_API_KEY"] = st.secrets.openai_api_key
from llama_index import LLMPredictor, ServiceContext, StorageContext, load_index_from_storage, QuestionAnswerPrompt
from langchain.chat_models import ChatOpenAI
import fitz  # PyMuPDF
from PIL import Image

st.set_page_config(
    page_title = "Documenter",
    page_icon = Image.open("./static/documenter.png"),
    initial_sidebar_state="expanded",
)

# pdf_path = "./static/NOBDATA_ChatGPT活用個別サービス開発資料.pdf"

type_to_index = {"展示会出展助成事業(PDF)":0, "NOBDATA_ChatGPT活用個別サービス開発資料(PPTX)":1}
type_to_path = {"展示会出展助成事業(PDF)":"./storage_pdf/", "NOBDATA_ChatGPT活用個別サービス開発資料(PPTX)":"./storage/"}
docu_to_pdf_path = {"展示会出展助成事業(PDF)":"./static/R5_tenjikaijyosei_boshuyoko_230403.pdf", "NOBDATA_ChatGPT活用個別サービス開発資料(PPTX)":"./static/NOBDATA_ChatGPT活用個別サービス開発資料.pdf"}

INTRO = "左側のテキストボックスに質問を入力しエンターキーを押すと、ＡＩが回答します。"

if "qa" not in st.session_state:
    st.session_state["qa"] = {"history": [{"role": "A", "msg": INTRO}]}

if "metadata" not in st.session_state:
    st.session_state["metadata"] = {"file_name": "", "slide_num": 0, "text": "", "score": ""}

if "pdf_page" not in st.session_state:
    st.session_state.pdf_page = list()

if "docu_index" not in st.session_state:
    st.session_state.docu_index = 0

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
def load_vector_db(docu_type):
    db_path = type_to_path[docu_type]
    llm_predictor = LLMPredictor(llm=ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo", streaming=True))
    # llm_predictor = LLMPredictor(llm=OpenAI(temperature=0, model_name="gpt-4", streaming=True))
    service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor)
    storage_context = StorageContext.from_defaults(persist_dir=db_path)
    index = load_index_from_storage(storage_context, service_context=service_context)
    return index

@st.cache_resource
def first_slide(docu_type):
    pdf_path = docu_to_pdf_path[docu_type]
    pdf_document = fitz.open(pdf_path)
    slide_data = pdf_document.load_page(0)
    image = slide_data.get_pixmap()
    image_data = image.tobytes("png")
    return image_data

@st.cache_data
def get_pdf_image(docu_type, page):
    pdf_path = docu_to_pdf_path[docu_type]
    pdf_document = fitz.open(pdf_path)
    page_data = pdf_document.load_page(page)
    image = page_data.get_pixmap()
    image_data = image.tobytes("png")
    return image_data
    
def store_del_msg():
    if st.session_state.user_input and st.session_state.qa["history"][-1]["role"] != "Q": # st.session_state.prev_q != st.session_state.user_input:
        st.session_state.qa["history"].append({"role": "Q", "msg": st.session_state.user_input}) # store
    st.session_state.user_input = ""  # del

# View (User Interface)
## Sidebar
st.sidebar.image("./static/documenter_logo.png", use_column_width="auto")

docu_index = st.session_state.docu_index
docu_type = st.sidebar.selectbox("文書を選んでください", ["展示会出展助成事業(PDF)", "NOBDATA_ChatGPT活用個別サービス開発資料(PPTX)"], index=docu_index)
st.session_state.docu_index = type_to_index[docu_type]

user_input = st.sidebar.text_input("質問をどうぞ", key="user_input", on_change=store_del_msg)
# st.sidebar.markdown("---")
if docu_type == "展示会出展助成事業(PDF)":
    if st.sidebar.button("助成事業の目的"):
        st.session_state.qa["history"].append({"role": "Q", "msg": "助成事業の目的を教えて下さい。"})
    # if st.sidebar.button("助成対象の経費"):
    #     st.session_state.qa["history"].append({"role": "Q", "msg": "助成対象の経費を教えて下さい。"})
    if st.sidebar.button("申請手順（表形式）"):
        st.session_state.qa["history"].append({"role": "Q", "msg": "申請手順を表にして下さい。"})
    slide_img = first_slide(docu_type)
    st.sidebar.image(slide_img, caption="展示会出展助成事業(令和５年度　東京都).pdf", use_column_width="auto")
elif docu_type == "NOBDATA_ChatGPT活用個別サービス開発資料(PPTX)":
    if st.sidebar.button("ＡＩおしゃべりロボって何ですか"):
        st.session_state.qa["history"].append({"role": "Q", "msg": "ＡＩおしゃべりロボって何ですか"})
    if st.sidebar.button("ＡＩおりこうロボって何ですか"):
        st.session_state.qa["history"].append({"role": "Q", "msg": "ＡＩおりこうロボって何ですか"})
    if st.sidebar.button("Documenterって何ですか"):
        st.session_state.qa["history"].append({"role": "Q", "msg": "Documenterって何ですか"})
    if st.sidebar.button("プロンプトセッターって何ですか"):
        st.session_state.qa["history"].append({"role": "Q", "msg": "プロンプトセッターって何ですか"})
    slide_img = first_slide(docu_type)
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
index = load_vector_db(docu_type)
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
        page_num = int(slide_num) if docu_type == "NOBDATA_ChatGPT活用個別サービス開発資料(PPTX)" else int(slide_num) - 1
        refer_pages = f"\n\n#{page_num}　{file_name}\n\n\n"
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
        with st.expander(f"表示"):
            file_name = st.session_state.metadata["file_name"]
            slide_num = st.session_state.metadata["slide_num"]
            text_cntx = st.session_state.metadata["text"]
            page_num = int(slide_num) if docu_type == "NOBDATA_ChatGPT活用個別サービス開発資料(PPTX)" else int(slide_num) - 1
            image_data = get_pdf_image(docu_type, page_num)
            # pdf_document = fitz.open(pdf_path)            
            # slide_data = pdf_document.load_page(slide_num)
            # image = slide_data.get_pixmap()
            # image_data = image.tobytes("png")
            st.image(image_data, caption=f"#{page_num}　{file_name}", use_column_width="auto")
            # st.write(text_cntx)
