import json
import logging

from dotenv import load_dotenv
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores.faiss import FAISS
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

with open('data.json', 'r') as f:
    results = json.load(f)['variable']

load_dotenv(dotenv_path='dotenv.env')

# Задаем модель чата
chat_model = ChatOpenAI(model='gpt-3.5-turbo-1106', temperature=0.2)

# Формируем векторную базу данных на основе текстового документа
loader = TextLoader(file_path='construction.txt', encoding='utf-8')
splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=200)
document = loader.load_and_split(text_splitter=splitter)
embedding = OpenAIEmbeddings()
vector_store = FAISS.from_documents(document, embedding=embedding)
store = vector_store.as_retriever(search_kwargs={'k': 1})

prompt_text = """Ты менеджер компании БрежневСтрой. 
Тебя зовут Никита, твоя задача консультировать клиентов основываясь 
на следующем контексте: {context}. Твои ответы не должны быть однотипными и ты не должен повторять то что написал клиент.
Так же, твоя основная задача вести разговор с клиентом по следующему сценарию: 
1. Ты должен изучить вопрос клиента и сказать что-то абстрактное, например что сразу не можем назвать цену, так как требуется замер или изучение дизайн - проекта.
2. Ты должен спросить у клиента номер телефона для обсуждения деталей
3. После того как человек даст свой номер телефона заверши разговор обещанием перезвонить в ближайшее время.
Если тебе задали вопрос не по теме, говори что ты можешь только помочь с ремонтом квартир и спрашивай остались ли вопросы.
Ты должен писать только Здравствуйте или Добрый день
Номер телефона проси только так - Пришлите, пожалуйста, ваш контактный телефон. Я перезвоню, обсудим стоимость и сроки
Ты не должен благодарить за обращение, ты должен поздороваться и сразу ответить на вопрос.
"""

prompt = ChatPromptTemplate.from_messages([
    ('system', prompt_text),
    MessagesPlaceholder(variable_name='chat_history'),
    ('human', '{input}')
])

# Формируем цепочку
chain = create_stuff_documents_chain(llm=chat_model, prompt=prompt)
retrieval_chain = create_retrieval_chain(store, chain)


# Делаем запрос
def process_chat(user_input, chat_history_list):
    response = retrieval_chain.invoke({
        'input': user_input,
        'chat_history': chat_history_list
    })
    return response['answer']


chat_history = []
new_results = {}

for key in results.keys():
    elem = ' '.join(results[key])
    try:
        res = process_chat(elem, chat_history)
        logging.basicConfig(
            filename='logs.log',  # Указываем имя файла, куда будут записываться логи
            filemode='a',  # Режим записи: 'a' - добавлять в конец файла, 'w' - перезаписывать файл
            format='%(asctime)s - %(levelname)s - %(message)s',  # Формат записи логов
            level=logging.INFO  # Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        )
        logging.info(f'Бот ответил пользователю {key}: {res}')
        if key in new_results.keys():
            new_results[key].append(res)
        else:
            new_results[key] = [res]

        chat_history.append(HumanMessage(content=elem))  # Добавляем по одному сообщению
        chat_history.append(AIMessage(content=res))  # Добавляем ответ AI

    except Exception as e:
        print(e)

with open('new.json', 'w') as f:
    json.dump({"new": new_results}, f)
