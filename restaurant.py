from tkinter import *
from tkinter.font import *
from tkinter import messagebox
import os



root = Tk()
pad_x = 5
pad_y = 5
width = root.winfo_screenwidth()
height = root.winfo_screenheight()
root.geometry('%dx%d' %(width, height))
root.state('zoomed')
root.grid_columnconfigure(0, weight=2)
root.grid_columnconfigure(1, weight=3)
root.grid_rowconfigure(0, weight=1)
root.title('Restaurant Manager')
myFont = Font(family='Calibri', size=16)



#region Database
import sqlite3

class Database:
    def __init__(self, db):
        self.__db_name = db
        self.connection = sqlite3.connect(db)
        self.cursor = self.connection.cursor()

        self.cursor.execute("""CREATE TABLE IF NOT EXISTS [Table_menu](
                                [ID] INT PRIMARY KEY NOT NULL UNIQUE,
                                [Name] VARCHAR(50) NOT NULL UNIQUE,
                                [Price] INT NOT NULL,
                                [isFood] BOOL NOT NULL) WITHOUT ROWID;
                            """)

        self.cursor.execute("""CREATE TABLE IF NOT EXISTS [Table_receipts](
                                [RECEIPT_ID] INT NOT NULL,
                                [MENU_ID] INT NOT NULL REFERENCES [Table_menu]([ID]),
                                [COUNT] INT,
                                [Price] INT);
                            """)

        self.cursor.execute("""
                            CREATE VIEW IF NOT EXISTS viewMenuReceipts AS
                            SELECT Table_receipts.RECEIPT_ID, Table_menu.Name, Table_receipts.Price,
                            Table_receipts.COUNT,(Table_receipts.COUNT * Table_receipts.Price) AS SUM
                            FROM Table_menu
                            INNER JOIN Table_receipts ON Table_menu.ID = Table_receipts.MENU_ID
                            """)

        self.connection.commit()
        self.connection.close()

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Table menu

    def fetch(self,):
        self.cursor.execute("SELECT * FROM Table_menu")
        rows = self.cursor.fetchall()
        return rows

    def insert(self, id, name, price, isFood):
        self.connection = sqlite3.connect(self.__db_name)
        self.cursor = self.connection.cursor()
        self.cursor.execute("INSERT INTO Table_menu VALUES (?, ?, ?, ?)"
                            , (id, name, price, isFood,))
        self.connection.commit()
        self.connection.close()

    def remove(self, id):
        self.cursor.execute("DELETE FROM Table_menu WHERE Id=?"
                            , (id,))
        self.connection.commit()

    def update(self, id, name, price):
        self.cursor.execute("UPDATE Table_menu SET Name=?, Price=? WHERE Id=?"
                            , (name, price, id,))
        self.connection.commit()
        self.connection.close()


    def getMenuItems(self, isFood):
        self.connection = sqlite3.connect(self.__db_name)
        self.cursor = self.connection.cursor()
        self.cursor.execute("SELECT * FROM Table_menu WHERE isFood = ?"
                            , (isFood,))
        result = self.cursor.fetchall()
        return result

    def getMaxReceiptId(self):
        self.connection = sqlite3.connect(self.__db_name)
        self.cursor = self.connection.cursor()
        self.cursor.execute("SELECT MAX(RECEIPT_ID) FROM Table_receipts")
        result = self.cursor.fetchall()
        return result

    def getMenuItemsByName(self, menuItemName):
        self.connection = sqlite3.connect(self.__db_name)
        self.cursor = self.connection.cursor()
        self.cursor.execute("SELECT * FROM Table_menu WHERE Name=?"
                            , (menuItemName,))
        result = self.cursor.fetchall()
        return result

    def insertIntoReceipts(self, receiptId, menuId, count, price):
        self.connection = sqlite3.connect(self.__db_name)
        self.cursor = self.connection.cursor()
        self.cursor.execute("INSERT INTO Table_receipts VALUES (?, ?, ?, ?)"
                            ,(receiptId, menuId, count, price,))
        self.connection.commit()
        self.connection.close()

    def getReceiptByReceiptIdMenuId(self, receiptId, menuId):
        self.connection = sqlite3.connect(self.__db_name)
        self.cursor = self.connection.cursor()
        self.cursor.execute("SELECT * FROM Table_receipts WHERE RECEIPT_ID = ? AND MENU_ID = ?"
                            ,(receiptId, menuId,))
        result = self.cursor.fetchall()
        return result

    def increaseCount(self, receiptId, menuId):
        self.connection = sqlite3.connect(self.__db_name)
        self.cursor = self.connection.cursor()
        self.cursor.execute("UPDATE Table_receipts SET COUNT = COUNT + 1 WHERE RECEIPT_ID = ? AND MENU_ID = ?"
                            , (receiptId, menuId,))
        self.connection.commit()
        self.connection.close()

    def getReceiptsByReceiptId(self, receiptId):
        self.connection = sqlite3.connect(self.__db_name)
        self.cursor = self.connection.cursor()
        self.cursor.execute("SELECT * FROM viewMenuReceipts WHERE RECEIPT_ID = ?" ,(receiptId,))
        result = self.cursor.fetchall()
        return result

    def deleteReceipt(self, receiptId, menuId):
        self.connection = sqlite3.connect(self.__db_name)
        self.cursor = self.connection.cursor()
        self.cursor.execute("DELETE FROM Table_receipts WHERE RECEIPT_ID = ? AND MENU_ID = ?", (receiptId, menuId))
        self.connection.commit()
        self.connection.close()

    def decreaseCount(self, receiptId, menuId):
        self.connection = sqlite3.connect(self.__db_name)
        self.cursor = self.connection.cursor()
        self.cursor.execute("UPDATE Table_receipts SET COUNT = COUNT - 1 WHERE RECEIPT_ID = ? AND MENU_ID = ? AND COUNT > 0"
                            , (receiptId, menuId))
        self.cursor.execute("DELETE FROM Table_receipts WHERE RECEIPT_ID = ? AND MENU_ID = ? AND COUNT = 0"
                            , (receiptId, menuId))
        self.connection.commit()
        self.connection.close()

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Table menu
#endregion


#region General
db = None
if os.path.isfile('restaurant.db') == False:
    db = Database('restaurant.db')
    db.insert(1,'Shit', '22000', True)
    db.insert(2, 'crap', '145', True)
    db.insert(3, 'Hamburger', '25', True)
    db.insert(4, 'Soda', '3', False)
    db.insert(5, 'Beer', '5', False)
else:
    db = Database('restaurant.db')


def loadReceipts(receiptId):
    listBox.delete(0, 'end')
    receipts = db.getReceiptsByReceiptId(receiptId)
    for receipt in receipts:
        listBox.insert(0, "%s %s %s %s" %(receipt[1], receipt[2], receipt[3], receipt[4]))

#-------------------------------------------------------------------------------------- Receipt Frame

receiptFrame = LabelFrame(root, text="Receipt",
font=myFont, padx=pad_x, pady=pad_y)
receiptFrame.grid(column=0, row=0, sticky='nsew')
receiptFrame.grid_columnconfigure(0, weight=1)
receiptFrame.grid_rowconfigure(1, weight=1)

entryOrderNum = Entry(receiptFrame, font=myFont, width=10, justify='center')
entryOrderNum.grid(column=0, row=0)

def entryKeyRelease(key):
    try:
        receiptId = int(entryOrderNum.get())
        loadReceipts(receiptId)
    except:
        listBox.delete(0, 'end')

entryOrderNum.bind('<KeyRelease>', entryKeyRelease)


maxReceiptNumber = db.getMaxReceiptId()
if maxReceiptNumber[0][0] == None:
    maxReceiptNumber = 0
else:
    maxReceiptNumber = int(maxReceiptNumber[0][0])
maxReceiptNumber += 1
entryOrderNum.insert(0, maxReceiptNumber)

listBox = Listbox(receiptFrame, font=myFont)
listBox.grid(column=0, row=1, sticky='nsew')


listBoxButtonsFrame = LabelFrame(receiptFrame, font=myFont)
listBoxButtonsFrame.grid(column=0, row=2, sticky='nsew')
listBoxButtonsFrame.grid_columnconfigure(0, weight=1)
listBoxButtonsFrame.grid_columnconfigure(1, weight=1)
listBoxButtonsFrame.grid_columnconfigure(2, weight=1)
listBoxButtonsFrame.grid_columnconfigure(3, weight=1)

#___________________________________________________________________________

def deleteReceiptItem():
    receiptId = int(entryOrderNum.get())
    menuItem = listBox.get(ACTIVE)
    menuItemName = menuItem.split(" ")[0]
    result = db.getMenuItemsByName(menuItemName)
    menuItemId = int(result[0][0])
    db.deleteReceipt(receiptId, menuItemId)
    loadReceipts(receiptId)

deleteButton = Button(listBoxButtonsFrame, text='Delete row',
font=myFont, command=deleteReceiptItem)

deleteButton.grid(column=0, row=0, sticky='nsew')

#___________________________________________________________________________

def newReceipt():
    listBox.delete(0, 'end')
    maxReceiptNumber = db.getMaxReceiptId()
    if maxReceiptNumber[0][0] == None:
        maxReceiptNumber = 0
    else:
        maxReceiptNumber = int(maxReceiptNumber[0][0])
    maxReceiptNumber += 1
    entryOrderNum.delete(0, 'end')
    entryOrderNum.insert(0, maxReceiptNumber)

newButton = Button(listBoxButtonsFrame, text='Add factor',
font=myFont, command=newReceipt)
newButton.grid(column=1, row=0, sticky='nsew')

#___________________________________________________________________________

def increaseItem():
    menuItemName = listBox.get(ACTIVE)
    result = db.getMenuItemsByName(menuItemName.split(" ")[0])
    menuItemId = result[0][0]
    receiptId = int(entryOrderNum.get())
    db.increaseCount(receiptId, menuItemId)
    loadReceipts(receiptId)

addButton = Button(listBoxButtonsFrame, text='+',
font=myFont, command=increaseItem)
addButton.grid(column=2, row=0, sticky='nsew')

#___________________________________________________________________________

def decreaseItem():
    menuItemName = listBox.get(ACTIVE)
    result = db.getMenuItemsByName(menuItemName.split(" ")[0])
    menuItemId = result[0][0]
    receiptId = int(entryOrderNum.get())
    db.decreaseCount(receiptId, menuItemId)
    loadReceipts(receiptId)


minusButton = Button(listBoxButtonsFrame, text='-',
font=myFont, command=decreaseItem)
minusButton.grid(column=3, row=0, sticky='nsew')

#-------------------------------------------------------------------------------------- Receipt Frame






#-------------------------------------------------------------------- Menu Frame

menuFrame = LabelFrame(root, text="Menu",
font=myFont, padx=pad_x, pady=pad_y)
menuFrame.grid(column=1, row=0, sticky='nsew')
menuFrame.grid_columnconfigure(0, weight=1)
menuFrame.grid_columnconfigure(1, weight=2)
menuFrame.grid_rowconfigure(0, weight=1)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Drink frame

drinkFrame = LabelFrame(menuFrame, text="Drinks", font=myFont)
drinkFrame.grid(column=0, row=0, sticky='nsew')
drinkFrame.grid_columnconfigure(0, weight=1)
drinkFrame.grid_rowconfigure(0, weight=1)
listboxDrinks = Listbox(drinkFrame, font=myFont, exportselection=False)
listboxDrinks.grid(sticky='nsew')
drinks = db.getMenuItems(False)
for drink in drinks:
    listboxDrinks.insert('end', drink[1])

def addDrink(event):
    drinkItem = db.getMenuItemsByName(listboxDrinks.get(ACTIVE))
    menuId = drinkItem[0][0]
    price = drinkItem[0][2]
    receiptId = int(entryOrderNum.get())
    result = db.getReceiptByReceiptIdMenuId(receiptId, menuId)
    if len(result) == 0:
        db.insertIntoReceipts(receiptId, menuId, 1, price)
    else:
        db.increaseCount(receiptId, menuId)

    loadReceipts(receiptId)

listboxDrinks.bind('<Double-Button>', addDrink)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Drink frame

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Food frame

foodFrame = LabelFrame(menuFrame, text="Foods", font=myFont)
foodFrame.grid(column=1, row=0, sticky='nsew')
foodFrame.grid_columnconfigure(0, weight=1)
foodFrame.grid_rowconfigure(0, weight=1)
listBoxFoods = Listbox(foodFrame, font=myFont, exportselection=False)
listBoxFoods.grid(sticky='nsew')
foods = db.getMenuItems(True)

def addFood(event):
    foodItem = db.getMenuItemsByName(listBoxFoods.get(ACTIVE))
    menuId = foodItem[0][0]
    price = foodItem[0][2]
    receiptId = int(entryOrderNum.get())
    result = db.getReceiptByReceiptIdMenuId(receiptId, menuId)
    if len(result) == 0:
        db.insertIntoReceipts(receiptId, menuId, 1, price)
    else:
        db.increaseCount(receiptId, menuId)

    loadReceipts(receiptId)

listBoxFoods.bind('<Double-Button>', addFood)

for food in foods:
    listBoxFoods.insert('end', food[1])

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Food frame

#-------------------------------------------------------------------- Menu Frame




#-------------------------------------------------------------------- Buttons Frame

buttonFrame = LabelFrame(root, font=myFont)
buttonFrame.grid(column=1, row=1)
from subprocess import call
def openCalculator():
    call('calc.exe')

def exitProgram():
    msgBox = messagebox.askquestion('Quit', 'Do you want to quit?'
, icon = 'warning')
    if msgBox == 'yes':
        root.destroy()

exitButton = Button(buttonFrame, text='Exit', font=myFont, fg='gray'
, command=exitProgram)
exitButton.grid(column=0, row=0)

calcButton = Button(buttonFrame, text='Calculator', font=myFont,
command=openCalculator)
calcButton.grid(column=1, row=0)
root.protocol("WM_DELETE_WINDOW", exitProgram)

#-------------------------------------------------------------------- Buttons Frame

root.mainloop()

#endregion