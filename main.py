import os
import sqlite3
import shutil
import re

# ReportLab Verification
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Kivy Framework Imports
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle

DB_FILE = "smart_khata_final.db"
CORE_DATA_DB = "house_hold_records_v4.db"

Window.softinput_mode = "below_target"

# =========================================================
# 💾 DATABASE SYSTEM LAYER
# =========================================================
def setup_databases():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
      (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, email TEXT UNIQUE, password TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS session 
      (id INTEGER PRIMARY KEY, email TEXT, is_logged_in INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

    conn2 = sqlite3.connect(CORE_DATA_DB)
    cursor2 = conn2.cursor()
    cursor2.execute("CREATE TABLE IF NOT EXISTS income (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, amount REAL, date TEXT, is_agri_sale TEXT)")
    cursor2.execute("""CREATE TABLE IF NOT EXISTS spendings (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, amount REAL, 
                    details TEXT, date TEXT, paid_status TEXT, unpaid_status TEXT, meter_reading TEXT)""")
    conn2.commit()
    conn2.close()
    
    if os.path.exists(CORE_DATA_DB):
        try: shutil.copy2(CORE_DATA_DB, "house_hold_backup.db")
        except: pass

setup_databases()

# =========================================================
# 🎨 HIGH CONTRAST CUSTOM UI COMPONENTS
# =========================================================
class ColoredScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.95, 0.96, 0.98, 1) 
            self.rect = Rectangle(size=Window.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.size = instance.size
        self.rect.pos = instance.pos

class StyledLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_name = "Roboto"
        self.size_hint_y = None
        self.height = 40
        self.bold = True
        self.color = (0.05, 0.08, 0.15, 1)

class StyledInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.multiline = False
        self.size_hint_y = None
        self.height = 45
        self.write_tab = False
        self.background_color = (1, 1, 1, 1) 
        self.foreground_color = (0, 0, 0, 1) 
        self.cursor_color = (0.11, 0.22, 0.54, 1)

class StyledButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = 50
        self.bold = True
        self.color = (1, 1, 1, 1) 
        self.background_normal = ''

# =========================================================
# 📔 SECURITY SCREENS
# =========================================================
class LoginScreen(ColoredScreen):
    def on_enter(self):
        self.clear_widgets()
        scroll = ScrollView(size_hint=(1, 1))
        layout = BoxLayout(orientation='vertical', padding=30, spacing=15, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        
        layout.add_widget(Label(text="Smart Khata", font_size=34, bold=True, color=(0.11, 0.22, 0.54, 1), size_hint_y=None, height=60))
        layout.add_widget(Label(text="Digital Diary System", font_size=15, bold=True, color=(0.3, 0.4, 0.5, 1), size_hint_y=None, height=30))
        
        layout.add_widget(StyledLabel(text="GMAIL ADDRESS:", text_size=(Window.width-60, None), halign="left"))
        self.email_input = StyledInput(hint_text="example@gmail.com")
        layout.add_widget(self.email_input)
        
        layout.add_widget(StyledLabel(text="PASSWORD:", text_size=(Window.width-60, None), halign="left"))
        self.pass_input = StyledInput(hint_text="Enter Password", password=True)
        layout.add_widget(self.pass_input)
        
        btn_login = StyledButton(text="Sign In", background_color=(0.11, 0.22, 0.54, 1))
        btn_login.bind(on_press=self.process_login)
        layout.add_widget(btn_login)
        
        btn_switch = Button(text="New User? Register Account", font_size=15, bold=True, background_color=(0,0,0,0), color=(0.15, 0.45, 0.85, 1), size_hint_y=None, height=45)
        btn_switch.bind(on_press=lambda x: setattr(self.manager, 'current', 'register'))
        layout.add_widget(btn_switch)
        
        scroll.add_widget(layout)
        self.add_widget(scroll)

    def process_login(self, instance):
        em = self.email_input.text.strip().lower()
        ps = self.pass_input.text.strip()
        if not em or not ps:
            self.show_popup("Error", "Please fill in all inputs.")
            return
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (em, ps))
        user = cursor.fetchone()
        conn.close()
        if user:
            self.manager.get_screen('dashboard').current_user_email = em
            self.manager.current = 'dashboard'
        else:
            self.show_popup("Access Denied", "Invalid Gmail or Password!")

    def show_popup(self, title, msg):
        pop = Popup(title=title, content=Label(text=msg), size_hint=(0.8, 0.4))
        pop.open()

class RegisterScreen(ColoredScreen):
    def on_enter(self):
        self.clear_widgets()
        scroll = ScrollView(size_hint=(1, 1))
        layout = BoxLayout(orientation='vertical', padding=30, spacing=12, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        
        layout.add_widget(Label(text="Register Account", font_size=26, bold=True, color=(0.05, 0.05, 0.1, 1), size_hint_y=None, height=45))
        
        layout.add_widget(StyledLabel(text="FULL USERNAME:", text_size=(Window.width-60, None), halign="left"))
        self.u_input = StyledInput()
        layout.add_widget(self.u_input)
        
        layout.add_widget(StyledLabel(text="GMAIL ADDRESS:", text_size=(Window.width-60, None), halign="left"))
        self.em_input = StyledInput(hint_text="must end with @gmail.com")
        layout.add_widget(self.em_input)
        
        layout.add_widget(StyledLabel(text="PASSWORD:", text_size=(Window.width-60, None), halign="left"))
        self.p_input = StyledInput(password=True)
        layout.add_widget(self.p_input)
        
        layout.add_widget(StyledLabel(text="RE-ENTER PASSWORD:", text_size=(Window.width-60, None), halign="left"))
        self.rp_input = StyledInput(password=True)
        layout.add_widget(self.rp_input)
        
        btn_reg = StyledButton(text="Complete Registration", background_color=(0.11, 0.22, 0.54, 1))
        btn_reg.bind(on_press=self.process_register)
        layout.add_widget(btn_reg)
        
        btn_back = Button(text="Back to Sign In", font_size=15, bold=True, background_color=(0,0,0,0), color=(0.3, 0.3, 0.4, 1), size_hint_y=None, height=40)
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'login'))
        layout.add_widget(btn_back)
        
        scroll.add_widget(layout)
        self.add_widget(scroll)

    def process_register(self, instance):
        u, em, p, rp = self.u_input.text.strip(), self.em_input.text.strip().lower(), self.p_input.text.strip(), self.rp_input.text.strip()
        if not u or not em or not p or not rp:
            self.show_popup("Error", "All fields are required.")
            return
        if not em.endswith("@gmail.com"):
            self.show_popup("Restriction", "Only official @gmail.com accounts allowed!")
            return
        if len(p) < 8 or not re.search(r"[A-Z]", p) or not re.search(r"[a-z]", p) or not re.search(r"\d", p) or not re.search(r"[!@#$%^&*()]", p):
            self.show_popup("Weak Password", "Rules failed! 8+ Chars, 1 Upper, 1 Lower, 1 Digit, 1 Special Char required.")
            return
        if p != rp:
            self.show_popup("Error", "Passwords do not match!")
            return
        try:
            conn = sqlite3.connect(DB_FILE)
            conn.cursor().execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (u, em, p))
            conn.commit()
            conn.close()
            self.show_popup("Success", "Account created successfully!")
            self.manager.current = 'login'
        except sqlite3.IntegrityError:
            self.show_popup("Error", "Email already exists.")

    def show_popup(self, title, msg):
        pop = Popup(title=title, content=Label(text=msg), size_hint=(0.8, 0.4))
        pop.open()

# =========================================================
# 🚜 MAIN DASHBOARD SCREEN
# =========================================================
class DashboardScreen(ColoredScreen):
    current_user_email = ""

    def on_enter(self):
        self.clear_widgets()
        main_layout = BoxLayout(orientation='vertical')
        
        top_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=55, padding=10, spacing=10)
        with top_bar.canvas.before:
            Color(0.11, 0.22, 0.54, 1) 
            self.nb_rect = Rectangle(size=top_bar.size, pos=top_bar.pos)
        top_bar.bind(size=lambda inst, val: setattr(self.nb_rect, 'size', val), pos=lambda inst, val: setattr(self.nb_rect, 'pos', val))
        
        top_bar.add_widget(Label(text=f"User: {self.current_user_email}", font_size=14, bold=True, halign="left", color=(1,1,1,1)))
        btn_logout = Button(text="Logout", bold=True, size_hint_x=None, width=90, background_color=(0.9, 0.2, 0.2, 1), background_normal='')
        btn_logout.bind(on_press=self.logout)
        top_bar.add_widget(btn_logout)
        main_layout.add_widget(top_bar)
        
        scroll = ScrollView(size_hint=(1, 1))
        content_layout = BoxLayout(orientation='vertical', padding=15, spacing=12, size_hint_y=None)
        content_layout.bind(minimum_height=content_layout.setter('height'))
        
        self.lbl_inc = Label(text="Total Income = 0.00", font_size=20, bold=True, color=(0.02, 0.55, 0.35, 1), size_hint_y=None, height=40)
        self.lbl_exp = Label(text="Total Spent = 0.00", font_size=20, bold=True, color=(0.8, 0.1, 0.1, 1), size_hint_y=None, height=40)
        self.lbl_bal = Label(text="Remaining Amount = 0.00", font_size=20, bold=True, color=(0.1, 0.3, 0.8, 1), size_hint_y=None, height=40)
        content_layout.add_widget(self.lbl_inc)
        content_layout.add_widget(self.lbl_exp)
        content_layout.add_widget(self.lbl_bal)
        
        content_layout.add_widget(Label(text="--- Agriculture & Ushr Card ---", font_size=16, bold=True, color=(0.05, 0.35, 0.2, 1), size_hint_y=None, height=35))
        self.lbl_agri_exp = Label(text="Total Agri Expense = 0.00", font_size=15, bold=True, color=(0.15, 0.15, 0.2, 1), size_hint_y=None, height=30)
        self.lbl_ushr = Label(text="Total Ushr Paid = 0.00", font_size=15, bold=True, color=(0.4, 0.25, 0.05, 1), size_hint_y=None, height=30)
        self.lbl_agri_net = Label(text="Agri Profit/Loss = 0.00", font_size=18, bold=True, color=(0.01, 0.4, 0.28, 1), size_hint_y=None, height=35)
        content_layout.add_widget(self.lbl_agri_exp)
        content_layout.add_widget(self.lbl_ushr)
        content_layout.add_widget(self.lbl_agri_net)
        
        btn_frame = BoxLayout(orientation='horizontal', size_hint_y=None, height=55, spacing=12)
        btn_add_inc = Button(text="Add Income", bold=True, background_color=(0.06, 0.65, 0.45, 1), background_normal='')
        btn_add_inc.bind(on_press=lambda x: self.go_to_entry("income"))
        btn_add_exp = Button(text="Add Expense", bold=True, background_color=(0.85, 0.15, 0.15, 1), background_normal='')
        btn_add_exp.bind(on_press=lambda x: self.go_to_entry("expense"))
        btn_frame.add_widget(btn_add_inc)
        btn_frame.add_widget(btn_add_exp)
        content_layout.add_widget(btn_frame)
        
        content_layout.add_widget(Label(text="View Historical Ledgers", font_size=15, bold=True, color=(0.3, 0.3, 0.4, 1), size_hint_y=None, height=35))
        
        btn_pdf = Button(text="📄 Generate System PDF Backup", bold=True, size_hint_y=None, height=50, background_color=(0.85, 0.3, 0.02, 1), background_normal='')
        btn_pdf.bind(on_press=self.generate_pdf)
        content_layout.add_widget(btn_pdf)
        
        btn_inc_rec = Button(text="Income History Records", bold=True, size_hint_y=None, height=45, background_color=(0.04, 0.5, 0.45, 1), background_normal='')
        btn_inc_rec.bind(on_press=lambda x: self.go_to_ledger("Income Records"))
        content_layout.add_widget(btn_inc_rec)
        
        categories = ["Agriculture", "Ushr", "Household", "Installment", "Fees", "Petrol", "Salami & Gifts"]
        for cat in categories:
            b = Button(text=f"{cat} Ledger", bold=True, size_hint_y=None, height=45, background_color=(0.22, 0.28, 0.35, 1), background_normal='')
            b.bind(on_press=lambda x, c=cat: self.go_to_ledger(c))
            content_layout.add_widget(b)
            
        scroll.add_widget(content_layout)
        main_layout.add_widget(scroll)
        self.add_widget(main_layout)
        self.calculate_live_totals()

    def calculate_live_totals(self):
        conn = sqlite3.connect(CORE_DATA_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(amount) FROM income")
        total_inc = cursor.fetchone()[0] or 0.0
        self.lbl_inc.text = f"Total Income = {total_inc:,.2f}"
        
        cursor.execute("SELECT SUM(amount) FROM spendings")
        total_exp = cursor.fetchone()[0] or 0.0
        self.lbl_exp.text = f"Total Spent = {total_exp:,.2f}"
        
        net_bal = total_inc - total_exp
        self.lbl_bal.text = f"Remaining Amount = {net_bal:,.2f}"
        
        cursor.execute("SELECT SUM(amount) FROM spendings WHERE category='Agriculture'")
        agri_spend = cursor.fetchone()[0] or 0.0
        self.lbl_agri_exp.text = f"Total Agri Expense = {agri_spend:,.2f}"
        
        cursor.execute("SELECT SUM(amount) FROM spendings WHERE category='Ushr'")
        ushr_spend = cursor.fetchone()[0] or 0.0
        self.lbl_ushr.text = f"Total Ushr Paid = {ushr_spend:,.2f}"
        
        cursor.execute("SELECT SUM(amount) FROM income WHERE is_agri_sale='Yes'")
        agri_inc = cursor.fetchone()[0] or 0.0
        agri_net = agri_inc - agri_spend - ushr_spend
        self.lbl_agri_net.text = f"Agri Profit/Loss = {agri_net:,.2f}"
        conn.close()

    def go_to_entry(self, mode):
        self.manager.get_screen('entry').entry_mode = mode
        self.manager.current = 'entry'

    def go_to_ledger(self, name):
        self.manager.get_screen('ledger').ledger_name = name
        self.manager.current = 'ledger'

    def generate_pdf(self, instance):
        if not REPORTLAB_AVAILABLE:
            self.show_popup("Error", "ReportLab module missing!")
            return
        pdf_filename = "Smart_Khata_System_Report.pdf"
        doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        story.append(Paragraph("Smart Khata Professional Ledger Report", styles['Heading1']))
        story.append(Spacer(1, 15))
        
        conn = sqlite3.connect(CORE_DATA_DB)
        cursor = conn.cursor()
        story.append(Paragraph("<b>Income Log History</b>", styles['Heading2']))
        inc_rows = [["Date", "Source/Title", "Amount Inflow"]]
        for r in cursor.execute("SELECT date, title, amount FROM income").fetchall():
            inc_rows.append([r[0], r[1], f"{r[2]:,.2f}"])
        t1 = Table(inc_rows, colWidths=[100, 250, 120])
        t1.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.green), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('GRID', (0,0), (-1,-1), 1, colors.grey)]))
        story.append(t1)
        story.append(Spacer(1, 20))
        
        story.append(Paragraph("<b>Spendings Outflow Log</b>", styles['Heading2']))
        exp_rows = [["Date", "Category", "Details", "Amount"]]
        for r in cursor.execute("SELECT date, category, details, amount FROM spendings").fetchall():
            exp_rows.append([r[0], r[1], r[2], f"{r[3]:,.2f}"])
        t2 = Table(exp_rows, colWidths=[90, 100, 180, 100])
        t2.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.red), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('GRID', (0,0), (-1,-1), 1, colors.grey)]))
        story.append(t2)
        conn.close()
        try:
            doc.build(story)
            self.show_popup("PDF Exported", f"Success! Backup generated safely as '{pdf_filename}'")
        except Exception as e:
            self.show_popup("Export Failed", str(e))

    def logout(self, instance):
        self.manager.current = 'login'

    def show_popup(self, title, msg):
        pop = Popup(title=title, content=Label(text=msg), size_hint=(0.8, 0.4))
        pop.open()

# =========================================================
# 🆕 KIVY DATA ENTRY SCREEN
# =========================================================
class EntryScreen(ColoredScreen):
    entry_mode = "income"

    def on_enter(self):
        self.clear_widgets()
        scroll = ScrollView(size_hint=(1, 1))
        self.layout = BoxLayout(orientation='vertical', padding=25, spacing=12, size_hint_y=None)
        self.layout.bind(minimum_height=self.layout.setter('height'))
        
        self.layout.add_widget(Label(text=f"--- ADD NEW {self.entry_mode.upper()} ---", font_size=22, bold=True, color=(0.11, 0.22, 0.54, 1), size_hint_y=None, height=45))
        
        self.layout.add_widget(StyledLabel(text="Date:", text_size=(Window.width-50, None), halign="left"))
        self.date_input = StyledInput(text="26-May-2026")
        self.layout.add_widget(self.date_input)
        
        if self.entry_mode == "income":
            self.layout.add_widget(StyledLabel(text="Income Source (Title):", text_size=(Window.width-50, None), halign="left"))
            self.title_input = StyledInput()
            self.layout.add_widget(self.title_input)
            
            self.layout.add_widget(StyledLabel(text="Amount:", text_size=(Window.width-50, None), halign="left"))
            self.amt_input = StyledInput()
            self.layout.add_widget(self.amt_input)
            
            self.layout.add_widget(StyledLabel(text="Agriculture Sale? (Yes / No):", text_size=(Window.width-50, None), halign="left"))
            self.agri_spin = Spinner(text="No", values=("No", "Yes"), size_hint_y=None, height=45, background_color=(0.2, 0.3, 0.5, 1), color=(1,1,1,1))
            self.layout.add_widget(self.agri_spin)
        else:
            self.layout.add_widget(StyledLabel(text="Category:", text_size=(Window.width-50, None), halign="left"))
            self.cat_spin = Spinner(text="Agriculture", values=("Agriculture", "Ushr", "Household", "Installment", "Fees", "Petrol", "Salami & Gifts"), size_hint_y=None, height=45, background_color=(0.2, 0.3, 0.5, 1), color=(1,1,1,1))
            self.cat_spin.bind(text=self.handle_dynamic_fields)
            self.layout.add_widget(self.cat_spin)
            
            self.layout.add_widget(StyledLabel(text="Details:", text_size=(Window.width-50, None), halign="left"))
            self.det_input = StyledInput()
            self.layout.add_widget(self.det_input)
            
            self.layout.add_widget(StyledLabel(text="Amount:", text_size=(Window.width-50, None), halign="left"))
            self.amt_input = StyledInput()
            self.layout.add_widget(self.amt_input)
            
            self.dyn_box = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
            self.dyn_box.bind(minimum_height=self.dyn_box.setter('height'))
            self.layout.add_widget(self.dyn_box)
            self.handle_dynamic_fields(None, "Agriculture")

        btn_save = StyledButton(text="Save Record Layout", background_color=(0.06, 0.6, 0.2, 1))
        btn_save.bind(on_press=self.save_transaction)
        self.layout.add_widget(btn_save)
        
        btn_cancel = StyledButton(text="Back to Dashboard", background_color=(0.45, 0.45, 0.45, 1))
        btn_cancel.bind(on_press=lambda x: setattr(self.manager, 'current', 'dashboard'))
        self.layout.add_widget(btn_cancel)
        
        scroll.add_widget(self.layout)
        self.add_widget(scroll)

    def handle_dynamic_fields(self, spinner, text):
        if not hasattr(self, 'dyn_box'): return
        self.dyn_box.clear_widgets()
        self.dyn_inputs = {}
        
        if text == "Agriculture":
            self.dyn_box.add_widget(StyledLabel(text="Paid Amount:", text_size=(Window.width-50, None), halign="left"))
            self.dyn_inputs['paid'] = StyledInput(text="0")
            self.dyn_box.add_widget(self.dyn_inputs['paid'])
            self.dyn_box.add_widget(StyledLabel(text="Unpaid Amount:", text_size=(Window.width-50, None), halign="left"))
            self.dyn_inputs['unpaid'] = StyledInput(text="0")
            self.dyn_box.add_widget(self.dyn_inputs['unpaid'])
        elif text == "Petrol":
            self.dyn_box.add_widget(StyledLabel(text="Meter Reading:", text_size=(Window.width-50, None), halign="left"))
            self.dyn_inputs['meter'] = StyledInput()
            self.dyn_box.add_widget(self.dyn_inputs['meter'])

    def save_transaction(self, instance):
        dt = self.date_input.text.strip()
        amt = self.amt_input.text.strip()
        if not dt or not amt: return
        
        conn = sqlite3.connect(CORE_DATA_DB)
        cursor = conn.cursor()
        
        if self.entry_mode == "income":
            t = self.title_input.text.strip()
            is_ag = self.agri_spin.text
            cursor.execute("INSERT INTO income (title, amount, date, is_agri_sale) VALUES (?, ?, ?, ?)", (t, float(amt), dt, is_ag))
        else:
            cat = self.cat_spin.text
            det = self.det_input.text.strip()
            p_v, up_v, m_v = "0", "0", ""
            if cat == "Agriculture":
                p_v = self.dyn_inputs['paid'].text.strip()
                up_v = self.dyn_inputs['unpaid'].text.strip()
            elif cat == "Petrol":
                m_v = self.dyn_inputs['meter'].text.strip()
                
            cursor.execute("INSERT INTO spendings (category, amount, details, date, paid_status, unpaid_status, meter_reading) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (cat, float(amt), det, dt, p_v, up_v, m_v))
        conn.commit()
        conn.close()
        self.manager.current = 'dashboard'

# =========================================================
# 📊 FIXED COLUMN MATRIX ENGINE (PERFECT ALIGNMENT)
# =========================================================
class LedgerScreen(ColoredScreen):
    ledger_name = ""
    selected_id = None
    all_row_containers = []

    def on_enter(self):
        self.clear_widgets()
        self.selected_id = None
        self.all_row_containers = []
        
        main_box = BoxLayout(orientation='vertical', padding=15, spacing=10)
        main_box.add_widget(Label(text=f"--- {self.ledger_name.upper()} ---", font_size=20, bold=True, color=(0.11, 0.22, 0.54, 1), size_hint_y=None, height=40))
        
        if self.ledger_name == "Income Records":
            headers = ["Date", "Source/Title", "Amount"]
            ratios = [0.25, 0.45, 0.30]
        elif self.ledger_name == "Agriculture":
            headers = ["Date", "Details", "Paid", "Unpaid", "Total"]
            ratios = [0.22, 0.24, 0.18, 0.18, 0.18]
        elif self.ledger_name == "Petrol":
            headers = ["Date", "Details", "Meter R.", "Amount"]
            ratios = [0.22, 0.28, 0.25, 0.25]
        else:
            headers = ["Date", "Details", "Amount"]
            ratios = [0.25, 0.45, 0.30]

        header_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=35)
        with header_box.canvas.before:
            Color(0.1, 0.1, 0.12, 1) 
            self.hd_rect = Rectangle(size=header_box.size, pos=header_box.pos)
        header_box.bind(size=lambda inst, val: setattr(self.hd_rect, 'size', val), pos=lambda inst, val: setattr(self.hd_rect, 'pos', val))
        
        for h, r in zip(headers, ratios):
            header_box.add_widget(Label(text=h, bold=True, size_hint_x=r, color=(1,1,1,1), font_size=14, halign="center"))
        main_box.add_widget(header_box)
        
        scroll = ScrollView(size_hint=(1, 1))
        self.rows_container = BoxLayout(orientation='vertical', spacing=6, size_hint_y=None)
        self.rows_container.bind(minimum_height=self.rows_container.setter('height'))
        
        conn = sqlite3.connect(CORE_DATA_DB)
        cursor = conn.cursor()
        
        if self.ledger_name == "Income Records":
            records = cursor.execute("SELECT id, date, title, amount FROM income").fetchall()
            for r in records:
                self.add_clean_row(r[0], [str(r[1]), str(r[2]), f"{r[3]:,.2f}"], ratios)
        elif self.ledger_name == "Agriculture":
            records = cursor.execute("SELECT id, date, details, amount, paid_status, unpaid_status FROM spendings WHERE category='Agriculture'").fetchall()
            for r in records:
                self.add_clean_row(r[0], [str(r[1]), str(r[2]), f"{float(r[4]):,.2f}", f"{float(r[5]):,.2f}", f"{r[3]:,.2f}"], ratios)
        elif self.ledger_name == "Petrol":
            records = cursor.execute("SELECT id, date, details, amount, meter_reading FROM spendings WHERE category='Petrol'").fetchall()
            for r in records:
                self.add_clean_row(r[0], [str(r[1]), str(r[2]), str(r[4]), f"{r[3]:,.2f}"], ratios)
        else:
            records = cursor.execute("SELECT id, date, details, amount FROM spendings WHERE category=?", (self.ledger_name,)).fetchall()
            for r in records:
                self.add_clean_row(r[0], [str(r[1]), str(r[2]), f"{r[3]:,.2f}"], ratios)
                
        conn.close()
        scroll.add_widget(self.rows_container)
        main_box.add_widget(scroll)
        
        self.btn_erase = StyledButton(text="🗑️ Erase Selected Record", background_color=(0.85, 0.15, 0.15, 1))
        self.btn_erase.bind(on_press=self.erase_record)
        main_box.add_widget(self.btn_erase)
        
        btn_back = StyledButton(text="Back to Dashboard", background_color=(0.35, 0.35, 0.35, 1))
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'dashboard'))
        main_box.add_widget(btn_back)
        self.add_widget(main_box)

    def add_clean_row(self, rid, cells_text, ratios):
        row_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=45)
        
        with row_box.canvas.before:
            Color(1, 1, 1, 1) 
            row_box.bg_color = Color(1, 1, 1, 1)
            row_box.bg_rect = Rectangle(size=row_box.size, pos=row_box.pos)
        row_box.bind(size=lambda inst, val: setattr(inst.bg_rect, 'size', val), pos=lambda inst, val: setattr(inst.bg_rect, 'pos', val))
        
        labels_references = []
        for text, ratio in zip(cells_text, ratios):
            lbl = Label(text=text, size_hint_x=ratio, color=(0,0,0,1), font_size=12, halign="center", valign="middle")
            lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
            row_box.add_widget(lbl)
            labels_references.append(lbl)
            
        click_trigger_btn = Button(background_color=(0,0,0,0), background_normal='', size_hint=(1, 1))
        click_trigger_btn.bind(on_press=lambda x: self.select_kivy_row_fixed(rid, row_box, labels_references))
        
        row_box.id_ref = rid
        row_box.labels_ref = labels_references
        self.all_row_containers.append(row_box)
        
        row_box.add_widget(click_trigger_btn)
        row_box.remove_widget(click_trigger_btn)
        row_box.bind(on_touch_down=lambda inst, touch: self.check_row_touch(inst, touch, rid, row_box, labels_references))
        
        self.rows_container.add_widget(row_box)

    def check_row_touch(self, instance, touch, rid, row_box, labels_references):
        if instance.collide_point(*touch.pos):
            self.select_kivy_row_fixed(rid, row_box, labels_references)
            return True
        return False

    def select_kivy_row_fixed(self, rid, clicked_row, labels_list):
        for row in self.all_row_containers:
            row.bg_color.rgb = (1, 1, 1)
            for lbl in row.labels_ref:
                lbl.color = (0,0,0,1)
                
        clicked_row.bg_color.rgb = (0.11, 0.22, 0.54)
        for lbl in labels_list:
            lbl.color = (1,1,1,1)
            
        self.selected_id = rid

    def erase_record(self, instance):
        if not self.selected_id: return
        conn = sqlite3.connect(CORE_DATA_DB)
        cursor = conn.cursor()
        if self.ledger_name == "Income Records":
            cursor.execute("DELETE FROM income WHERE id=?", (self.selected_id,))
        else:
            cursor.execute("DELETE FROM spendings WHERE id=?", (self.selected_id,))
        conn.commit()
        conn.close()
        self.selected_id = None
        self.on_enter()

# =========================================================
# ⚙️ APP RUNNER ENGINE CONTROL
# =========================================================
class SmartKhataApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(RegisterScreen(name='register'))
        sm.add_widget(DashboardScreen(name='dashboard'))
        sm.add_widget(EntryScreen(name='entry'))
        sm.add_widget(LedgerScreen(name='ledger'))
        return sm

if __name__ == '__main__':
    SmartKhataApp().run()
