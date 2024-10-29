#region imports
from tkinter import *
from tkinter.font import *
import tkinter as tk 
from tkinter import LabelFrame, Button, messagebox 
from subprocess import call
import os
from typing import Final
from telegram import Update, ForceReply
from telegram.ext import Application, CommandHandler, ContextTypes
#endregion

#region others

# Constants 

BACKGROUND_COLOR = "#171717" 
FONT_FAMILY = 'Calibri' 
FONT_SIZE = 16 

# Initialize the root window 

root = Tk() 
root.configure(bg=BACKGROUND_COLOR)

# Screen dimensions 

pad_x, pad_y = 5, 5 
width, height = root.winfo_screenwidth(), root.winfo_screenheight() 
root.geometry(f'{width}x{height}') 
root.state('zoomed')

# Configure grid layout 

root.grid_columnconfigure(0, weight=2) 
root.grid_columnconfigure(1, weight=3) 
root.grid_rowconfigure(0, weight=1) 

# Window title 

root.title('Restaurant Manager') 

# Font settings 

myFont = Font(family=FONT_FAMILY, size=FONT_SIZE)

#endregion

#region Database

import sqlite3

class Database:
    def __init__(self, db):
        self.__db_name = db
        self.connect()
        self.setup_database()

    def connect(self):
        self.connection = sqlite3.connect(self.__db_name)
        self.cursor = self.connection.cursor()

    def close(self):
        self.connection.close()

    def setup_database(self):
        # Create Menu table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS TABLE_MENU (
                                ID INTEGER PRIMARY KEY NOT NULL UNIQUE,
                                NAME TEXT NOT NULL UNIQUE,
                                PRICE INTEGER NOT NULL,
                                ISFOOD INTEGER NOT NULL) 
                                WITHOUT ROWID''')

        # Create Receipts table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS TABLE_RECEIPTS (
                                RECEIPT_ID INTEGER NOT NULL,
                                MENU_ID INTEGER NOT NULL REFERENCES TABLE_MENU(ID),
                                COUNT INTEGER,
                                PRICE INTEGER)''')

        # Create View for Menu Receipts
        self.cursor.execute('''CREATE VIEW IF NOT EXISTS viewMenuReceipts AS
                                SELECT TABLE_RECEIPTS.RECEIPT_ID,
                                TABLE_MENU.NAME,
                                TABLE_RECEIPTS.PRICE,
                                TABLE_RECEIPTS.COUNT,
                                (TABLE_RECEIPTS.COUNT * TABLE_RECEIPTS.PRICE) AS SUM
                                FROM TABLE_MENU
                                INNER JOIN TABLE_RECEIPTS ON TABLE_MENU.ID = TABLE_RECEIPTS.MENU_ID''')
        self.connection.commit()

    def fetch(self):
        self.connect()
        self.cursor.execute("SELECT * FROM TABLE_MENU")
        rows = self.cursor.fetchall()
        self.close()
        return rows

    def insert(self, id, name, price, is_food):
        with sqlite3.connect(self.__db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO TABLE_MENU VALUES (?, ?, ?, ?)", (id, name, price, is_food))
            conn.commit()

    def remove(self, id):
        with sqlite3.connect(self.__db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM TABLE_MENU WHERE ID=?", (id,))
            conn.commit()

    def update(self, id, name, price):
        with sqlite3.connect(self.__db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE TABLE_MENU SET NAME=?, PRICE=? WHERE ID=?", (name, price, id))
            conn.commit()

    def get_menu_items(self, is_food):
        with sqlite3.connect(self.__db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM TABLE_MENU WHERE ISFOOD=?", (is_food,))
            result = cursor.fetchall()
        return result

    def get_max_receipt_id(self):
        with sqlite3.connect(self.__db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(RECEIPT_ID) FROM TABLE_RECEIPTS")
            result = cursor.fetchone()
        return result[0] if result[0] is not None else 0

    def get_menu_items_by_name(self, menu_item_name):
        with sqlite3.connect(self.__db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM TABLE_MENU WHERE NAME=?", (menu_item_name,))
            result = cursor.fetchall()
        return result

    def insert_into_receipts(self, receipt_id, menu_id, count, price):
        with sqlite3.connect(self.__db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO TABLE_RECEIPTS VALUES (?, ?, ?, ?)", (receipt_id, menu_id, count, price))
            conn.commit()

    def get_receipt_by_receipt_id_menu_id(self, receipt_id, menu_id):
        with sqlite3.connect(self.__db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM TABLE_RECEIPTS WHERE RECEIPT_ID=? AND MENU_ID=?", (receipt_id, menu_id))
            result = cursor.fetchall()
        return result

    def increase_count(self, receipt_id, menu_id):
        with sqlite3.connect(self.__db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE TABLE_RECEIPTS SET COUNT=COUNT+1 WHERE RECEIPT_ID=? AND MENU_ID=?", (receipt_id, menu_id))
            conn.commit()

    def get_receipts_by_receipt_id(self, receipt_id):
        with sqlite3.connect(self.__db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM viewMenuReceipts WHERE RECEIPT_ID=?", (receipt_id,))
            result = cursor.fetchall()
        return result

    def delete_receipt(self, receipt_id, menu_id):
        with sqlite3.connect(self.__db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM TABLE_RECEIPTS WHERE RECEIPT_ID=? AND MENU_ID=?", (receipt_id, menu_id))
            conn.commit()

    def decrease_count(self, receipt_id, menu_id):
        with sqlite3.connect(self.__db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE TABLE_RECEIPTS SET COUNT=COUNT-1 WHERE RECEIPT_ID=? AND MENU_ID=? AND COUNT > 0", (receipt_id, menu_id))
            cursor.execute("DELETE FROM TABLE_RECEIPTS WHERE RECEIPT_ID=? AND MENU_ID=? AND COUNT=0", (receipt_id, menu_id))
            conn.commit()


db = None
if os.path.isfile('restaurant.db') == False:
    db = Database('restaurant.db')
    db.insert(1,'Pizza', '22', True)
    db.insert(2, 'Cheeseburger', '9', True)
    db.insert(3, 'Hamburger', '8', True)
    db.insert(4, 'Soda', '3', False)
    db.insert(5, 'Beer', '5', False)
else:
    db = Database('restaurant.db')


def load_receipts(receipt_id):
    try:
        # Clear the listbox
        listBox.delete(0, 'end')
        
        # Fetch receipts from the database
        receipts = db.get_receipts_by_receipt_id(receipt_id)
        
        # Insert each receipt into the listbox
        for receipt in receipts:
            listBox.insert(0, f"{receipt[1]} {receipt[2]} {receipt[3]} {receipt[4]}")
    except Exception as e:
        print(f"Error loading receipts: {e}")


#endregion

#region bot

# Constants
TOKEN: Final = '7599295073:AAF7QCxtVupmbkf89QbdjwbHvC48_w0ecB8'
DATABASE_FILE: Final = 'restaurant.db'

# Function to start the bot
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! I'm your Restaurant Bot. Use /foods to see the food menu and /drinks to see the drink menu.",
        reply_markup=ForceReply(selective=True),
    )

# Fetch menu items
menu_foods = db.get_menu_items(True)
menu_drinks = db.get_menu_items(False)

# Function to display food menu
async def food_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for food in menu_foods:
        await update.message.reply_text(food[1])

# Function to display drink menu
async def drink_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for drink in menu_drinks:
        await update.message.reply_text(drink[1])

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('foods', food_command))
    app.add_handler(CommandHandler('drinks', drink_command))
    app.run_polling(poll_interval=1)
#endregion

#region Receipt

# Constants
BACKGROUND_COLOR = "#171717"
FOREGROUND_COLOR = "#e0e0e0"
HIGHLIGHT_COLOR = "black"
PAD_X, PAD_Y = 5, 5
FONT = ('Calibri', 16)


receiptFrame = LabelFrame(root, text="Receipt", font=FONT, padx=PAD_X, pady=PAD_Y, bg=BACKGROUND_COLOR, fg=FOREGROUND_COLOR)
receiptFrame.grid(column=0, row=0, sticky='nsew')
receiptFrame.grid_columnconfigure(0, weight=1)
receiptFrame.grid_rowconfigure(1, weight=1)

entryOrderNum = Entry(receiptFrame, font=FONT, width=10, justify='center', bg=BACKGROUND_COLOR, fg=FOREGROUND_COLOR,
                        highlightthickness=1, highlightbackground=HIGHLIGHT_COLOR)
entryOrderNum.grid(column=0, row=0)

def entry_key_release(event):
    try:
        receipt_id = int(entryOrderNum.get())
        load_receipts(receipt_id)
    except ValueError:
        listBox.delete(0, 'end')

entryOrderNum.bind('<KeyRelease>', entry_key_release)

# Initialize max receipt number
maxReceiptNumber = db.get_max_receipt_id()
maxReceiptNumber = maxReceiptNumber if maxReceiptNumber is not None else 0
maxReceiptNumber += 1
entryOrderNum.insert(0, maxReceiptNumber)

listBox = Listbox(receiptFrame, font=FONT, bg=BACKGROUND_COLOR, fg=FOREGROUND_COLOR, highlightthickness=3, highlightbackground=HIGHLIGHT_COLOR)
listBox.grid(column=0, row=1, sticky='nsew')

listBoxButtonsFrame = LabelFrame(receiptFrame, font=FONT, bg=BACKGROUND_COLOR, fg=FOREGROUND_COLOR, highlightthickness=3, highlightbackground=HIGHLIGHT_COLOR)
listBoxButtonsFrame.grid(column=0, row=2, sticky='nsew')
listBoxButtonsFrame.grid_columnconfigure(0, weight=1)
listBoxButtonsFrame.grid_columnconfigure(1, weight=1)
listBoxButtonsFrame.grid_columnconfigure(2, weight=1)
listBoxButtonsFrame.grid_columnconfigure(3, weight=1)

def load_receipts(receipt_id):
    try:
        listBox.delete(0, 'end')
        receipts = db.get_receipts_by_receipt_id(receipt_id)
        for receipt in receipts:
            listBox.insert(0, f"{receipt[1]} {receipt[2]} {receipt[3]} {receipt[4]}")
    except Exception as e:
        print(f"Error loading receipts: {e}")

def delete_receipt_item():
    try:
        receipt_id = int(entryOrderNum.get())
        menu_item = listBox.get(ACTIVE)
        menu_item_name = menu_item.split(" ")[0]
        result = db.get_menu_items_by_name(menu_item_name)
        menu_item_id = int(result[0][0])
        db.delete_receipt(receipt_id, menu_item_id)
        load_receipts(receipt_id)
    except Exception as e:
        print(f"Error deleting receipt item: {e}")

deleteButton = Button(listBoxButtonsFrame, text='Delete row', font=FONT, command=delete_receipt_item, bg=BACKGROUND_COLOR, fg=FOREGROUND_COLOR,
                        highlightthickness=3, highlightbackground=HIGHLIGHT_COLOR)
deleteButton.grid(column=0, row=0, sticky='nsew')

def new_receipt():
    listBox.delete(0, 'end')
    max_receipt_number = db.get_max_receipt_id()
    max_receipt_number = max_receipt_number if max_receipt_number is not None else 0
    max_receipt_number += 1
    entryOrderNum.delete(0, 'end')
    entryOrderNum.insert(0, max_receipt_number)

newButton = Button(listBoxButtonsFrame, text='Add factor', font=FONT, command=new_receipt, bg=BACKGROUND_COLOR, fg=FOREGROUND_COLOR,
                    highlightthickness=3, highlightbackground=HIGHLIGHT_COLOR)
newButton.grid(column=1, row=0, sticky='nsew')

def increase_item():
    try:
        menu_item_name = listBox.get(ACTIVE)
        result = db.get_menu_items_by_name(menu_item_name.split(" ")[0])
        menu_item_id = result[0][0]
        receipt_id = int(entryOrderNum.get())
        db.increase_count(receipt_id, menu_item_id)
        load_receipts(receipt_id)
    except Exception as e:
        print(f"Error increasing item count: {e}")

addButton = Button(listBoxButtonsFrame, text='+', font=FONT, command=increase_item, bg=BACKGROUND_COLOR, fg=FOREGROUND_COLOR,
                    highlightthickness=3, highlightbackground=HIGHLIGHT_COLOR)
addButton.grid(column=2, row=0, sticky='nsew')

def decrease_item():
    try:
        menu_item_name = listBox.get(ACTIVE)
        result = db.get_menu_items_by_name(menu_item_name.split(" ")[0])
        menu_item_id = result[0][0]
        receipt_id = int(entryOrderNum.get())
        db.decrease_count(receipt_id, menu_item_id)
        load_receipts(receipt_id)
    except Exception as e:
        print(f"Error decreasing item count: {e}")

minusButton = Button(listBoxButtonsFrame, text='-', font=FONT, command=decrease_item, bg=BACKGROUND_COLOR, fg=FOREGROUND_COLOR,
                        highlightthickness=3, highlightbackground=HIGHLIGHT_COLOR)
minusButton.grid(column=3, row=0, sticky='nsew')

#endregion

#region menu

# Menu Frame
menuFrame = LabelFrame(root, text="Menu", font=FONT, padx=PAD_X, pady=PAD_Y, bg=BACKGROUND_COLOR, fg=FOREGROUND_COLOR,
                        highlightthickness=3, highlightbackground=HIGHLIGHT_COLOR)
menuFrame.grid(column=1, row=0, sticky='nsew')
menuFrame.grid_columnconfigure(0, weight=1)
menuFrame.grid_columnconfigure(1, weight=2)
menuFrame.grid_rowconfigure(0, weight=1)

# Drink Frame
drinkFrame = LabelFrame(menuFrame, text="Drinks", font=FONT, bg=BACKGROUND_COLOR, fg=FOREGROUND_COLOR,
                        highlightthickness=3, highlightbackground=HIGHLIGHT_COLOR)
drinkFrame.grid(column=0, row=0, sticky='nsew')
drinkFrame.grid_columnconfigure(0, weight=1)
drinkFrame.grid_rowconfigure(0, weight=1)

listboxDrinks = Listbox(drinkFrame, font=FONT, exportselection=False, bg=BACKGROUND_COLOR, fg=FOREGROUND_COLOR,
                        highlightthickness=3, highlightbackground=HIGHLIGHT_COLOR)
listboxDrinks.grid(sticky='nsew')

drinks = db.get_menu_items(False)
for drink in drinks:
    listboxDrinks.insert('end', drink[1])

def add_drink(event):
    try:
        drink_item = db.get_menu_items_by_name(listboxDrinks.get(ACTIVE))
        menu_id = drink_item[0][0]
        price = drink_item[0][2]
        receipt_id = int(entryOrderNum.get())
        result = db.get_receipt_by_receipt_id_menu_id(receipt_id, menu_id)
        if not result:
            db.insert_into_receipts(receipt_id, menu_id, 1, price)
        else:
            db.increase_count(receipt_id, menu_id)
        load_receipts(receipt_id)
    except Exception as e:
        print(f"Error adding drink: {e}")

listboxDrinks.bind('<Double-Button>', add_drink)

# Food Frame
foodFrame = LabelFrame(menuFrame, text="Foods", font=FONT, bg=BACKGROUND_COLOR, fg=FOREGROUND_COLOR,
                        highlightthickness=3, highlightbackground=HIGHLIGHT_COLOR)
foodFrame.grid(column=1, row=0, sticky='nsew')
foodFrame.grid_columnconfigure(0, weight=1)
foodFrame.grid_rowconfigure(0, weight=1)

listBoxFoods = Listbox(foodFrame, font=FONT, exportselection=False, bg=BACKGROUND_COLOR, fg=FOREGROUND_COLOR,
                        highlightthickness=3, highlightbackground=HIGHLIGHT_COLOR)
listBoxFoods.grid(sticky='nsew')

foods = db.get_menu_items(True)
for food in foods:
    listBoxFoods.insert('end', food[1])

def add_food(event):
    try:
        food_item = db.get_menu_items_by_name(listBoxFoods.get(ACTIVE))
        menu_id = food_item[0][0]
        price = food_item[0][2]
        receipt_id = int(entryOrderNum.get())
        result = db.get_receipt_by_receipt_id_menu_id(receipt_id, menu_id)
        if not result:
            db.insert_into_receipts(receipt_id, menu_id, 1, price)
        else:
            db.increase_count(receipt_id, menu_id)
        load_receipts(receipt_id)
    except Exception as e:
        print(f"Error adding food: {e}")

listBoxFoods.bind('<Double-Button>', add_food)

def load_receipts(receipt_id):
    try:
        listBox.delete(0, 'end')
        receipts = db.get_receipts_by_receipt_id(receipt_id)
        for receipt in receipts:
            listBox.insert(0, f"{receipt[1]} {receipt[2]} {receipt[3]} {receipt[4]}")
    except Exception as e:
        print(f"Error loading receipts: {e}")


#endregion

#region Buttons

# Button Frame
buttonFrame = LabelFrame(root, font=FONT, bg=BACKGROUND_COLOR, fg=FOREGROUND_COLOR,
                            highlightthickness=3, highlightbackground=HIGHLIGHT_COLOR)
buttonFrame.grid(column=1, row=1, padx=PAD_X, pady=PAD_Y)

# Function to open calculator
def open_calculator():
    try:
        call('calc.exe')
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open calculator: {e}")

# Function to exit program
def exit_program():
    try:
        msgBox = messagebox.askquestion('Quit', 'Do you want to quit?', icon='warning')
        if msgBox == 'yes':
            root.destroy()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to exit: {e}")

# Exit Button
exitButton = Button(buttonFrame, text='Exit', font=FONT, bg=BACKGROUND_COLOR, fg=FOREGROUND_COLOR,
                    command=exit_program, highlightthickness=3, highlightbackground=HIGHLIGHT_COLOR)
exitButton.grid(column=0, row=0, padx=PAD_X, pady=PAD_Y)

# Calculator Button
calcButton = Button(buttonFrame, text='Calculator', font=FONT, command=open_calculator, bg=BACKGROUND_COLOR,
                    fg=FOREGROUND_COLOR, highlightthickness=3, highlightbackground=HIGHLIGHT_COLOR)
calcButton.grid(column=1, row=0, padx=PAD_X, pady=PAD_Y)

# Handle window close event
root.protocol("WM_DELETE_WINDOW", exit_program)

#endregion

root.mainloop()