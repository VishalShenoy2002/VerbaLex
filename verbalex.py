from langchain_community.document_loaders import TextLoader, PDFPlumberLoader
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
import psycopg2
import json


class VerbaLex:
    
    def __init__(self,avatar="Alex"):
        
        with open('avatars.json','r') as f:
            self.__avatar_data = json.load(f)
            f.close()
            
        
        self.__llm = ChatGroq(model="llama3-70b-8192", temperature=0, max_tokens=None, timeout=None, max_retries=2)
        self.__avatars = [avatar['avatar']['avatar-name'] for avatar in self.__avatar_data]
        
        self.__avatar = avatar
        self.__avatar_prompt = self.__get_prompt(self.__avatar)
        
        self.__template_str = self.__avatar_prompt + '''
        
        Here’s the message from the user: "{message}"
        Your response:
        '''
        
        self.__prompt = PromptTemplate(input_variables=["message"], template=self.__template_str) 
        self.__chain = self.__prompt | self.__llm
        
    def __get_prompt(self, avatar):
        for avatar_details in self.__avatar_data:
            if avatar_details['avatar']['avatar-name'].lower() == avatar.lower():
                return avatar_details['avatar']['avatar-prompt']  
                break
    @property
    def avatars(self):
        return self.__avatars
    
    @property
    def avatar(self):
        return self.__avatar
    
    @avatar.setter
    def avatar(self, avatar):
        if avatar in self.__avatars:
            self.__avatar = avatar
            self.__prompt = self.__get_prompt(avatar)
            # self.__chain = self.__prompt | self.__llm
        else:
            raise ValueError("This avatar doesn't exist")
    
    def generate(self, message):
        self.__response = self.__chain.invoke({"message": message})
        
        self.__response = self.__response.content
        return self.__response
         
        
