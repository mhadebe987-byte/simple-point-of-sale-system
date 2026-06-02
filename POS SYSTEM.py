from tkinter import *
from tkinter import messagebox
import mysql.connector
import datetime
import bcrypt


# ---------- DATABASE CONNECTION ----------
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="mzamo1010H!",
        database="pos_system"
    )

# ---------- PASSWORD UTILITIES ----------
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# ---------- SIGN-UP AND LOGIN ----------
def signup():
    username = entry_user.get()
    password = entry_pass.get()
    db = connect_db()
    cursor = db.cursor()
    try:
        hashed = hash_password(password).decode('utf-8')
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed))
        db.commit()
        messagebox.showinfo("Success", "Account created!")
    except mysql.connector.errors.IntegrityError:
        messagebox.showerror("Error", "Username already exists.")
    db.close()

def login():
    username = entry_user.get()
    password = entry_pass.get()
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT user_id, password FROM users WHERE username=%s", (username,))
    result = cursor.fetchone()
    db.close()
    if result and check_password(password, result[1]):
        messagebox.showinfo("Login", "Welcome and Thank you for Visiting Us!")
        app.destroy()
        launch_pos(result[0], username)
    else:
        messagebox.showerror("Login Failed", "Invalid credentials.")

# ---------- POS SYSTEM ----------
def launch_pos(user_id, username):
    def update_date():
        date_label.config(text=datetime.datetime.now().strftime('%B %d, %Y'))

    def clear():
        nonlocal total_price
        textbox.delete('1.0', END)
        pay_here.delete(0, END)
        total_price = 0
        change.config(text='Change : R0')
        total.config(text='Total : R0')

    def add_to_cart(product_index):
        nonlocal total_price
        db = connect_db()
        cursor = db.cursor()
        cursor.execute("SELECT stock, price, name FROM products WHERE product_id = %s", (product_index + 1,))
        result = cursor.fetchone()
        stock_qty, price, name = result
        if stock_qty > 0:
            total_price += price
            cursor.execute("UPDATE products SET stock = stock - 1 WHERE product_id = %s", (product_index + 1,))
            cursor.execute("INSERT INTO purchases (user_id, product_id, quantity, purchase_time) VALUES (%s, %s, %s, NOW())",
                           (user_id, product_index + 1, 1))
            db.commit()
            total.config(text=f'Total : R{total_price}')
            textbox.insert(END, f'{name} -> R{price} | Remaining: {stock_qty - 1}\n')
        else:
            messagebox.showwarning("Out of Stock", f"{name} is out of stock.")
        db.close()

    def checkout():
        nonlocal total_price
        try:
            payment = float(pay_here.get())
            if payment <= 0 or payment < total_price:
                messagebox.showerror("Insufficient", "Insufficient Amount!")
                return
            change_amt = payment - total_price
            change.config(text=f'Change : R{change_amt}')
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            answer = messagebox.askyesno("SLIP", "Want a slip?")
            if answer:
                slip = (
                    f'Items Purchased\nUser: {username}\nDate: {now}\n\n'
                    f'{textbox.get("1.0", END)}'
                    f'Total Price: R{total_price}\nPaid: R{payment}\nChange: R{change_amt}\n\n'
                    'THANK YOU FOR SHOPPING WITH US!'
                )
                messagebox.showinfo("Slip", slip)
        except ValueError:
            messagebox.showerror("ERROR!", "Please enter a valid amount!")

    def show_admin():
        db = connect_db()
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]

        cursor.execute("SELECT name, stock FROM products")
        stock_info = cursor.fetchall()
        db.close()

        stock_text = "\n".join([f"{name}: {qty} left" for name, qty in stock_info])
        messagebox.showinfo("Admin Dashboard", f"Total Users: {user_count}\n\nStock Levels:\n{stock_text}")

    def Exit():
        pos_root.destroy()

    # ---------- GUI ----------
    pos_root = Tk()
    pos_root.title('POINT OF SALE SYSTEM')
    pos_root.config(bg='#000E1B')

    date_label = Label(pos_root)
    date_label.pack()
    update_date()

    frame = Frame(pos_root, bg='#3AD80A')
    frame.pack(pady=10)

    Label(frame, text=f'WELCOME {username.upper()}! 🛒', font=('Ink Free', 15, 'bold')).grid(row=0, columnspan=3)

    textbox = Text(frame, width=50, height=15, fg="#3AD80A", bg='#02343F')
    textbox.insert('1.0', 'Cart :\n')
    textbox.grid(row=1, column=2)

    total = Label(frame, text='Total : R0', font=('arial', 10, 'bold'))
    total.grid(row=2, columnspan=3)

    Label(frame, text='Enter Payment:', font=('arial', 10, 'bold')).grid(row=3, columnspan=3)
    pay_here = Entry(frame)
    pay_here.grid(row=4, columnspan=3)

    change = Label(frame, text='Change : R0', font=('arial', 10, 'bold'))
    change.grid(row=5, columnspan=3)

    # Product Buttons
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT name FROM products")
    product_names = [row[0] for row in cursor.fetchall()]
    db.close()

    button_frame = Frame(pos_root, bg='#000E1B')
    button_frame.pack()

    total_price = 0
    for i, name in enumerate(product_names):
        Button(button_frame, text=name, bg='darkgray', fg='blue',
               command=lambda index=i: add_to_cart(index)).grid(row=i // 2, column=i % 2, padx=5, pady=5)

    Button(frame, text='Checkout', bg='darkgray', fg='blue', command=checkout).grid(row=6, columnspan=3, pady=3)
    Button(frame, text='Clear', bg='darkgray', fg='blue', command=clear).grid(row=7, columnspan=3, pady=3)
    Button(frame, text='Admin Dashboard', bg='black', fg='white', command=show_admin).grid(row=10, columnspan=3, pady=3)
    Button(frame, text='Exit', bg='darkgray', fg='blue', command=Exit).grid(row=8, columnspan=3)

    pos_root.mainloop()

# ---------- LOGIN WINDOW ----------
app = Tk()
#app.config(bg='navyblue')
app.geometry('500x400')
#login_window.title("Login / Sign Up")
#login_window.configure(bg='lime')
Label(app,text='Login or Sign-Up',font=('Arial',20,'bold')).pack(pady=10)

Label(app, text="Username").pack()
entry_user = Entry(app)
entry_user.pack(pady=5)

Label(app, text="Password").pack()
entry_pass = Entry(app, show="*")
entry_pass.pack(pady=5)

Button(app, text="Sign Up" ,command=signup).pack(pady=5)
Button(app, text="Login", command=login).pack(pady=5)

Label(app,text='NOTE :',font=('Arial',14,'bold'),bg='yellow').pack(pady=2)
Label(app,text="Don't have an account , sign-up then login\n\n Already have an account just enter your credentials and Login ",font=('Arial',10,'bold')).pack(pady=3)

app.mainloop()
