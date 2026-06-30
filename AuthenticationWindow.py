from tkinter import *
from tkinter import ttk
from UserDatabase import *
from HashTable import *
class AuthenticationWindow:
    def __init__(self):
        self.window=Tk()
        self.window.geometry('400x500')
        self.window.title('Graph Transformations Visualiser')
        self.db=UserDatabase()
        self.hash_table=HashTable()
        self.LogInButton()
        self.SignUpButton()
    
    def BuildTitle(self):
        title=Label(self.window,text='Graph Transformation Visualiser',font=('Arial',16))
        title.grid(row=0,column=0,columnspan=2,pady=40,padx=20)    
    
    def BuildButtons(self):
        login_button=ttk.Button(self.window,text='Log In',command=self.OpenLogin)
        login_button.grid(row=1,column=0,padx=10,pady=10)
        signup_button=ttk.Buttom(self.window,text='Sign Up',command=self.OpenSignUp)
        signup_button.grid(row=1,column=1,padx=10,pady=10)

    def OpenLogin(self):
        LoginWindow(self.window,self.db,self.hash_table)

    def SignUpButton(self):
        SignUpWindow(self.window,self.db,self.hash_table)