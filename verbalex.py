from langchain_community.document_loaders import TextLoader, PDFPlumberLoader
from langchain.prompts import MessagesPlaceholder, ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_community.chat_message_histories import PostgresChatMessageHistory
import psycopg2
import json
import uuid
import sys

class VerbaLex:
    
    def __init__(self,avatar="Alex",history=True,chat_context=5):
        
        with open('avatars.json','r') as f:
            self.__avatar_data = json.load(f)
            f.close()
        
        
        self.__history = history
        
        self.__llm = ChatGroq(model="llama3-70b-8192", temperature=0, max_tokens=None, timeout=None, max_retries=2)
        self.__avatars = [avatar['avatar']['avatar-name'] for avatar in self.__avatar_data]
        
        self.__avatar = avatar
        self.__avatar_prompt = self.__get_prompt(self.__avatar)
        
        if self.__history == True:
            self.__chat_context = chat_context * 2 if chat_context is not None  else 0
            self.__conn = psycopg2.connect(host="localhost",port=5432,user="postgres",password="asdasd123",database="verbalex")
            self.__cursor = self.__conn.cursor()
            self.__session_id = uuid.uuid4()
            
            self.__add_message(self.__avatar_prompt,"system")
            

        
        self.__messages = [("system", self.__avatar_prompt), MessagesPlaceholder("chat_history"), ("human", "{message}") ] if self.__history == True else [("system", self.__avatar_prompt), ("human", "{message}") ]
        self.__prompt = ChatPromptTemplate.from_messages(messages=self.__messages)

        self.__chain = self.__prompt | self.__llm
        
    def __get_prompt(self, avatar):
        for avatar_details in self.__avatar_data:
            if avatar_details['avatar']['avatar-name'].lower() == avatar.lower():
                return avatar_details['avatar']['avatar-prompt']  
                break
    def __get_title(self, avatar):
        for avatar_details in self.__avatar_data:
            if avatar_details['avatar']['avatar-name'].lower() == avatar.lower():
                return avatar_details['avatar']['avatar-title']  
                break
            
    def __add_message(self,message,message_type):
        try:
            self.__cursor.execute("INSERT INTO message_store (session_id, message, message_type) VALUES (%s, %s, %s);", (str(self.__session_id), message, message_type))
            self.__conn.commit()
        except psycopg2.Error as e:
            self.__conn.rollback()
            pass
        
    def __get_previous_messages(self):
        # Fetch the last 10 messages for the current session
        query = f"SELECT message_type, message FROM message_store WHERE session_id = %s ORDER BY created_at DESC LIMIT {self.__chat_context}"
        self.__cursor.execute(query, (str(self.__session_id),))
        recorded_messages = self.__cursor.fetchall()
        return [("human",message) if message_type == "user" else (message_type.lower(),message) for message_type,message in recorded_messages[::-1]]  
 
    @property
    def avatars(self):
        return self.__avatars
    
    @property
    def avatar(self):
        return self.__avatar
    
    @property
    def about(self):
        title = self.__get_title(self.avatar)
        return f'{self.avatar} - {title}'
    
    @avatar.setter
    def avatar(self, avatar):
        if avatar in self.__avatars:
            self.__avatar = avatar
            self.__prompt = self.__get_prompt(avatar)
            # self.__chain = self.__prompt | self.__llm
        else:
            raise ValueError("This avatar doesn't exist")
    
    def generate(self, message):
        
        if self.__history == True:
            recorded_messages = self.__get_previous_messages()
            self.__add_message(message=message, message_type="user")
            self.__response = self.__chain.invoke({"message": message,"chat_history":recorded_messages})
            
            self.__response = self.__response.content
            self.__add_message(message=self.__response, message_type="AI")
        else:
            self.__response = self.__chain.invoke({"message": message})
            self.__response = self.__response.content
        
        return self.__response
    
    @property     
    def message_history(self):
        query = "SELECT message_type,message FROM message_store WHERE session_id = %s ORDER BY created_at"
        self.__cursor.execute(query,(f'{self.__session_id}',))
        recorded_messages = self.__cursor.fetchall()
        messages = []
        for message_type, message in recorded_messages:
            message_type = "human" if message_type.lower() == "user" else message_type.lower()
            messages.append((message_type,message))
            
        return messages
        
if __name__ == "__main__":
    bot = VerbaLex(avatar="Lara",history=True)
    print(f"Chat with {bot.about}")
    while True:
        try:
            message = input("> ")
            response = bot.generate(message)
            print(f'\n{bot.avatar}: {response}',end='\n\n')
        except KeyboardInterrupt:
            sys.exit('Exitting Chat!')
    # print(ChatPromptTemplate.from_messages([("system","Hi"),("system","Hi"),("system","Hi")]))
    # print()
        
