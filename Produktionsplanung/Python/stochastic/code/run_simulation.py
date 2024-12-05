from PyQt5.QtWidgets import ( QApplication, QMainWindow, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget, 
                             QGridLayout, QSizePolicy,QDesktopWidget, QShortcut, QFileDialog, QMessageBox)
from PyQt5.QtGui import QFont, QPixmap , QKeySequence
from model_Sto_backend import *
from PyQt5.QtCore import Qt
import sys
import json

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

       # Bildschirmgröße ermitteln
        screen_geometry = QDesktopWidget().availableGeometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()

        # Fenstergröße auf Bildschirmgröße setzen
        self.resize(screen_width, screen_height)
        self.setWindowFlags(Qt.FramelessWindowHint)

        # Hauptlayout
        main_layout = QVBoxLayout()

        # Horizontaler Header mit Logo und Text
        header_layout = QHBoxLayout()

        # Logo
        logo_label = QLabel()
        logo_pixmap = QPixmap("Produktionsplanung\Python\deterministic\code\logo.png").scaled(60, 60, Qt.KeepAspectRatio)  # Replace with your logo path
        logo_label.setPixmap(logo_pixmap)
        header_layout.addWidget(logo_label, alignment=Qt.AlignLeft)
        
        # Text
        title_label = QLabel("Operations Management Group\nInstitute of Management and Economics")
        title_label.setFont(QFont("Arial", 14, QFont.Normal))
        header_layout.addWidget(title_label, alignment=Qt.AlignLeft)

        # Platzhalter, um Header linksbündig zu halten
        header_layout.addStretch()

        main_layout.addLayout(header_layout)

        # 2. Layout: Input Fields for T, n, m
        self.param_inputs = {}
        self.params = {
            "T (periods)": 12 , "n (products)": 6, "m (factors)": 4, "m_a (secondary factors)": 2, "q (samples)": 100,
        }

        param_layout = QHBoxLayout()
        for param, value in self.params.items():
            label = QLabel(param)
            label.setFont(QFont("Georgia", 10, QFont.Bold))
            input_field = QLineEdit(str(value))
            input_field.setMaximumWidth(100)
            self.param_inputs[param] = input_field
            param_layout.addWidget(input_field)
            param_layout.addWidget(label)
            
        submit_button = QPushButton("Generate Input Fields")
        submit_button.setFont(QFont("Arial", 10, QFont.Bold))
        submit_button.setStyleSheet("background-color: lightgray;")
        submit_button.clicked.connect(self.generate_fields)
        param_layout.addWidget(submit_button)

        main_layout.addLayout(param_layout)

        # 3. Reserved Layout for dynamic fields (Demand, Availability, etc.)
        self.dynamic_layout =  QGridLayout()
        self.dynamic_widgets = {}

        main_layout.addLayout(self.dynamic_layout)

        # 4. Layout for Buttons (Run Solver and Save Results)
        button_layout = QHBoxLayout()

        # Run Solver Button
        self.run_button = QPushButton("Run MPS_CE")
        self.run_button.setFont(QFont("Arial", 10, QFont.Bold))
        self.run_button.setStyleSheet("background-color: lightgray;")
        self.run_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.run_button.clicked.connect(self.run_solver)
        button_layout.addWidget(self.run_button)

        # Save Results Button
        self.save_button = QPushButton("Save Parameters")
        self.save_button.setFont(QFont("Arial", 10, QFont.Bold))
        self.save_button.setStyleSheet("background-color: lightgray;")
        self.save_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.save_button.clicked.connect(self.save_data)
        button_layout.addWidget(self.save_button)

        # Load Results Button
        self.load_button = QPushButton("Load Parameters")
        self.load_button.setFont(QFont("Arial", 10, QFont.Bold))
        self.load_button.setStyleSheet("background-color: lightgray;")
        self.load_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.load_button.clicked.connect(self.load_data)
        button_layout.addWidget(self.load_button)

        main_layout.addLayout(button_layout)

        # 5. Results Layout
        self.results_layout = QVBoxLayout()
        self.results_label = QLabel("")
        self.results_layout.addWidget(self.results_label)

        main_layout.addLayout(self.results_layout)
        # not necessary setting
        adlayout = QVBoxLayout()
        addlabel = QLabel("\n\n\n\n")
        adlayout.addWidget(addlabel)

        main_layout.addLayout(adlayout)

        adlayout = QVBoxLayout()
        addlabel = QLabel("\n\n\n\n")
        adlayout.addWidget(addlabel)

        main_layout.addLayout(adlayout)

        adlayout = QVBoxLayout()
        addlabel = QLabel("\n\n\n\n\t")
        adlayout.addWidget(addlabel)

        main_layout.addLayout(adlayout)

        adlayout = QVBoxLayout()
        addlabel = QLabel("\n\n\n\n\t")
        adlayout.addWidget(addlabel)

        main_layout.addLayout(adlayout)

        adlayout = QVBoxLayout()
        addlabel = QLabel("\n\n\n\n")
        adlayout.addWidget(addlabel)

        main_layout.addLayout(adlayout)

        adlayout = QVBoxLayout()
        addlabel = QLabel("\n\n\n\n")
        adlayout.addWidget(addlabel)

        main_layout.addLayout(adlayout)

        adlayout = QVBoxLayout()
        addlabel = QLabel("\n\n\n\n")
        adlayout.addWidget(addlabel)

        main_layout.addLayout(adlayout)

        # Set up main window layout
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # generate default field
        self.generate_fields()

        # Add a shortcut to close the window (Ctrl+Q)
        close_shortcut = QShortcut (QKeySequence("Ctrl+Q"), self)
        close_shortcut.activated.connect(self.close)

    def update_performance_label(self):
         result_text = "<table style=border-collapse: collapse; margin: 10px;>"
         for param, value in self.results.items():
            result_text += f""" <tr>
                        <td style="padding-right: 20px; text-align: left; font-weight: bold;">{param}:</td>
                        <td style="text-align: right; padding-left: 20px; color: green;">{value:.4f}</td>
                        </tr>
                                """
         result_text += "</table>"  
         self.results_label.setText(result_text)

    def clear_layout(self, layout):
        while layout.count():
             child = layout.takeAt(0)
             if child.widget():
                  child.widget().deleteLater()
             elif child.layout():
                  self.clear_layout(child.layout())
    
    def save_data(self):
        T  = int(self.params["T (periods)"]) # number of periods
        n = int(self.params["n (products)"]) # number of products
        m = int(self.params["m (factors)"])  # number of production factors
        alpha = int(self.params["m_a (secondary factors)"])
        I_A = range(alpha)

        d = [[0.0]*T]*n
        for j in range(n):
            for t in range(T):
                  d[j][t] = float(self.dynamic_widgets[f"d-{j+1}-{t+1}"].text())
        p = [0.0]*n
        for j in range(n):
             p[j] = float(self.dynamic_widgets[f"p-{j+1}"].text())
        k = [0.0]*n
        for j in range(n):
             k[j] = float(self.dynamic_widgets[f"k-{j+1}"].text())
        h = [0.0]*n
        for j in range(n):
            h[j] = float(self.dynamic_widgets[f"h-{j+1}"].text())
        b = [0.0]*alpha
        for i in range(alpha):
            b[i] = float(self.dynamic_widgets[f"b-{i+1}"].text())   
        c = [0.0]*alpha
        for i in range(alpha):
            c[i] = float(self.dynamic_widgets[f"c-{i+1}"].text()) 
        A = [[0.0]*T]*m
        for i in range(m):
          for t in range(T):
                A[i][t] = float(self.dynamic_widgets[f"d-{j+1}-{t+1}"].text())
        a = [[0.0]*n]*m
        for i in range(m):
            for j in range(n):
                a[i][j] = float(self.dynamic_widgets[f"a-{i+1}-{j+1}"].text())
        I_minus_I_A = [i for i in range(m) if i not in I_A]  
        R_fix = [[0.0]*T]*(m-alpha)
        for i in range(m-alpha):
            for t in range(T):
                R_fix[i][t] = float(self.dynamic_widgets[f"R_fix-{i+1}-{t+1}"].text())
        x_a = [0.0]*n
        for j in range(n):
              x_a[j] = float(self.dynamic_widgets[f"x_a-{j+1}"].text()) 
        R_a = [0.0]*alpha
        for i in range(alpha):
            R_a[i] = float(self.dynamic_widgets[f"Ra-{i+1}"].text())
        
        data_to_save = {
            "T": T,
            "n": n,
            "m": m,
            "alpha":alpha,
            "d": d,     
            "p": p,      
            "k": k,       
            "h": h,       
            "b": b,       
            "c": c,       
            "A": A,       
            "a": a,       
            "I_minus_I_A": I_minus_I_A, 
            "R_fix": R_fix,
            "x_a": x_a,
            "R_a": R_a
        }

        with open("results_data.json", "w") as file:
             json.dump(data_to_save, file, indent=4)

    def load_data(self):

        with open("results_data.json", "r") as file:
           loaded_data = json.load(file)
    
        # Clear previous dynamic widgets
        self.clear_layout(self.dynamic_layout)
       
        self.params["T (periods)"] = loaded_data["T"]
        self.params["n (products)"] = loaded_data["n"]
        self.params["m (factors)"] = loaded_data["m"]
        self.params["m_a (secondary factors)"] = loaded_data["alpha"]

        self.param_inputs["T (periods)"].setText(str(self.params["T (periods)"]))
        self.param_inputs["n (products)"].setText(str(self.params["n (products)"]))
        self.param_inputs["m (factors)"].setText(str(self.params["m (factors)"]))
        self.param_inputs["m_a (secondary factors)"].setText(str(self.params["m_a (secondary factors)"]))
        
        T = self.params["T (periods)"]
        n = self.params["n (products)"]
        m = self.params["m (factors)"]
        alpha = self.params["m_a (secondary factors)"]
        
        label_widget = QLabel(f"d (Demand):")
        label_widget.setFont(QFont("Georgia", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, 0, 0)
        for j in range(n):
            for t in range(T):
                field = QLineEdit(str(loaded_data["d"][j][t]))
                field.setMaximumWidth(50)
                self.dynamic_layout.addWidget(field, j, t + 1)  # Add fields next to the label
                self.dynamic_widgets[f"d-{j+1}-{t+1}"] = field
        
        label_widget = QLabel(f"p (Price):")
        label_widget.setFont(QFont("Georgia", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+1, 0)
        for j in range(n):
                field = QLineEdit(str(loaded_data["p"][j]))
                field.setMaximumWidth(50)
                self.dynamic_layout.addWidget(field, n+1, j + 1)  # Add fields next to the label
                self.dynamic_widgets[f"p-{j+1}"] = field
        
        label_widget = QLabel(f"k (production cost):")
        label_widget.setFont(QFont("Georgia", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+2, 0)
        for j in range(n):
                field = QLineEdit(str(loaded_data["k"][j]))
                field.setMaximumWidth(50)
                self.dynamic_layout.addWidget(field, n+2, j + 1)  # Add fields next to the label
                self.dynamic_widgets[f"k-{j+1}"] = field     
        
        label_widget = QLabel(f"h (holding cost):")
        label_widget.setFont(QFont("Georgia", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+3, 0)
        for j in range(n):
                field = QLineEdit(str(loaded_data[f"h"][j]))
                field.setMaximumWidth(50)
                self.dynamic_layout.addWidget(field, n+3, j + 1)  # Add fields next to the label
                self.dynamic_widgets[f"h-{j+1}"] = field    
        
        label_widget = QLabel(f"A (avaibility):")
        label_widget.setFont(QFont("Georgia", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+4, 0)
        for i in range(m):
            for t in range(T):
                field = QLineEdit(str(loaded_data["A"][j][t]))
                field.setMaximumWidth(50)
                self.dynamic_layout.addWidget(field, n+i+4, t + 1)  # Add fields next to the label
                self.dynamic_widgets[f"A-{i+1}-{t+1}"] = field   

        label_widget = QLabel(f"x_a (initial inventory products):")
        label_widget.setFont(QFont("Georgia", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+m+5, 0)
        for j in range(n):
                field = QLineEdit(str(loaded_data[f"x_a"][j]))
                field.setMaximumWidth(50)
                self.dynamic_layout.addWidget(field, n+m+5, j + 1)  # Add fields next to the label
                self.dynamic_widgets[f"x_a-{j+1}"] = field   
        
        label_widget = QLabel(f"a (production coefficients):")
        label_widget.setFont(QFont("Georgia", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+m+6, 0)
        for i in range(m):
            for j in range(n):
                field = QLineEdit(str(loaded_data["a"][i][j]))
                field.setMaximumWidth(50)
                self.dynamic_layout.addWidget(field, n+m+i+6, j + 1)  # Add fields next to the label
                self.dynamic_widgets[f"a-{i+1}-{j+1}"] = field
        
        label_widget = QLabel(f"R_a (initial inventory levels of secondary materials):")
        label_widget.setFont(QFont("Georgia", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+2*m+7, 0)
        for i in range(alpha):
                field = QLineEdit(str(loaded_data["R_a"][i]))
                field.setMaximumWidth(50)
                self.dynamic_layout.addWidget(field, n+2*m+7, i + 1)
                self.dynamic_widgets[f"Ra-{i+1}"] = field
        
        label_widget = QLabel(f"b (procurement cost of secondary materials):")
        label_widget.setFont(QFont("Georgia", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+2*m+8, 0)
        for i in range(alpha):
                field = QLineEdit(str(loaded_data["b"][i]))
                field.setMaximumWidth(50)
                self.dynamic_layout.addWidget(field, n+2*m+8, i + 1)
                self.dynamic_widgets[f"b-{i+1}"] = field
        
        label_widget = QLabel(f"c (procurement cost of corresponding primary materials):")
        label_widget.setFont(QFont("Georgia", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+2*m+9, 0)
        for i in range(alpha):
                field = QLineEdit(str(loaded_data["c"][i]))
                field.setMaximumWidth(50)
                self.dynamic_layout.addWidget(field, n+2*m+9, i + 1)
                self.dynamic_widgets[f"c-{i+1}"] = field
        
        label_widget = QLabel(f"Rfix (capacity of non-secondary production factors):")
        label_widget.setFont(QFont("Georgia", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+2*m+10, 0)
        for i in range(m-alpha):
            for t in range(T):
                field = QLineEdit(str(loaded_data["R_fix"][i][t]))
                field.setMaximumWidth(50)
                self.dynamic_layout.addWidget(field, n+2*m+10+i, t + 1 )
                self.dynamic_widgets[f"R_fix-{i+1}-{t+1}"] = field
        
    def generate_fields(self):
        # Clear previous dynamic widgets
        self.clear_layout(self.dynamic_layout)
       
        # Get values for T, n, m
        T = int(self.param_inputs["T (periods)"].text())
        n = int(self.param_inputs["n (products)"].text())
        m = int(self.param_inputs["m (factors)"].text())
        alpha = int(self.param_inputs["m_a (secondary factors)"].text())
        
        label_widget = QLabel(f"d (Demand)")
        label_widget.setFont(QFont("Georgia", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, 0, 0)
        for j in range(n):
            for t in range(T):
                field = QLineEdit()
                field.setMaximumWidth(50)
                self.dynamic_layout.addWidget(field, j, t + 1)  # Add fields next to the label
                self.dynamic_widgets[f"d-{j+1}-{t+1}"] = field
        
        label_widget = QLabel(f"p (Price)")
        label_widget.setFont(QFont("Georgia", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+1, 0)
        for j in range(n):
                field = QLineEdit()
                field.setMaximumWidth(50)
                self.dynamic_layout.addWidget(field, n+1, j + 1)  # Add fields next to the label
                self.dynamic_widgets[f"p-{j+1}"] = field
        
        label_widget = QLabel(f"k (production cost)")
        label_widget.setFont(QFont("Georgia", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+2, 0)
        for j in range(n):
                field = QLineEdit()
                field.setMaximumWidth(50)
                self.dynamic_layout.addWidget(field, n+2, j + 1)  # Add fields next to the label
                self.dynamic_widgets[f"k-{j+1}"] = field     

        label_widget = QLabel(f"h (holding cost)")
        label_widget.setFont(QFont("Georgia", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+3, 0)
        for j in range(n):
                field = QLineEdit()
                field.setMaximumWidth(50)
                self.dynamic_layout.addWidget(field, n+3, j + 1)  # Add fields next to the label
                self.dynamic_widgets[f"h-{j+1}"] = field    
        
        label_widget = QLabel(f"A (avaibility)")
        label_widget.setFont(QFont("Georgia", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+4, 0)
        for i in range(m):
            for t in range(T):
                field = QLineEdit()
                field.setMaximumWidth(50)
                self.dynamic_layout.addWidget(field, n+i+4, t + 1)  # Add fields next to the label
                self.dynamic_widgets[f"A-{i+1}-{t+1}"] = field   

        label_widget = QLabel(f"x_a (initial inventory products)")
        label_widget.setFont(QFont("Georgia", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+m+5, 0)
        for j in range(n):
                field = QLineEdit()
                field.setMaximumWidth(50)
                self.dynamic_layout.addWidget(field, n+m+5, j + 1)  # Add fields next to the label
                self.dynamic_widgets[f"x_a-{j+1}"] = field   
        
        label_widget = QLabel(f"a (production coefficients)")
        label_widget.setFont(QFont("Georgia", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+m+6, 0)
        for i in range(m):
            for j in range(n):
                field = QLineEdit()
                field.setMaximumWidth(50)
                self.dynamic_layout.addWidget(field, n+m+i+6, j + 1)  # Add fields next to the label
                self.dynamic_widgets[f"a-{i+1}-{j+1}"] = field
        
        label_widget = QLabel(f"R_a (initial inventory levels of secondary materials)")
        label_widget.setFont(QFont("Georgia", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+2*m+7, 0)
        for i in range(alpha):
                field = QLineEdit()
                field.setMaximumWidth(50)
                self.dynamic_layout.addWidget(field, n+2*m+7, i + 1)
                self.dynamic_widgets[f"Ra-{i+1}"] = field
        
        label_widget = QLabel(f"b (procurement cost of secondary materials)")
        label_widget.setFont(QFont("Georgia", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+2*m+8, 0)
        for i in range(alpha):
                field = QLineEdit()
                field.setMaximumWidth(50)
                self.dynamic_layout.addWidget(field, n+2*m+8, i + 1)
                self.dynamic_widgets[f"b-{i+1}"] = field
        
        label_widget = QLabel(f"c (procurement cost of corresponding primary materials)")
        label_widget.setFont(QFont("Georgia", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+2*m+9, 0)
        for i in range(alpha):
                field = QLineEdit()
                field.setMaximumWidth(50)
                self.dynamic_layout.addWidget(field, n+2*m+9, i + 1)
                self.dynamic_widgets[f"c-{i+1}"] = field
        
        label_widget = QLabel(f"Rfix (capacity of non-secondary production factors)")
        label_widget.setFont(QFont("Georgia", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+2*m+10, 0)
        for i in range(m-alpha):
            for t in range(T):
                field = QLineEdit()
                field.setMaximumWidth(50)
                self.dynamic_layout.addWidget(field, n+2*m+10+i, t + 1 )
                self.dynamic_widgets[f"R_fix-{i+1}-{t+1}"] = field
    
    def show_error_message(self, message):
        # Zeige eine Fehlermeldung an
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setText(message)
        msg_box.setWindowTitle("Fehler")
        msg_box.exec_()    

    def run_solver(self):
        # Versuche, alle Parameter-Werte zu konvertieren
        params = {}
        for key, input_field in self.param_inputs.items():
            try:
                # Versuche den Text in eine Zahl umzuwandeln
                params[key] = float(input_field.text())

                # Überprüfe, ob der Wert negativ ist
                if params[key] < 0:
                    self.show_error_message(f"The Entry for '{key}' cannot be negative. Please enter a valid number.")
                    return  # Verhindere die Ausführung des Solvers, wenn der Wert negativ ist
           
            except ValueError:
                # Falls es einen Fehler gibt (keine gültige Zahl), zeige ein Fehler-Popup
                self.show_error_message(f"The Entry for '{key}' is not valid. Please enter a valid number.")
                return  # Verhindere die Ausführung des Solvers, wenn Fehler aufgetreten ist
        
        T  = int(params["T (periods)"]) # number of periods
        n = int(params["n (products)"]) # number of products
        m = int(params["m (factors)"])  # number of production factors
        alpha = int(params["m_a (secondary factors)"])
        q  = int(params["q (samples)"])
        try:
            d = [[0.0]*T]*n
            for j in range(n):
                for t in range(T):
                        d[j][t] = float(self.dynamic_widgets[f"d-{j+1}-{t+1}"].text())*(1.1-np.sin(j+2*np.pi*t/T))
            p = [0.0]*n
            for j in range(n):
                p[j] = float(self.dynamic_widgets[f"p-{j+1}"].text())
            k = [0.0]*n
            for j in range(n):
                k[j] = float(self.dynamic_widgets[f"k-{j+1}"].text())
            h = [0.0]*n
            for j in range(n):
                h[j] = float(self.dynamic_widgets[f"h-{j+1}"].text())
            b = [0.0]*alpha
            for i in range(alpha):
                b[i] = float(self.dynamic_widgets[f"b-{i+1}"].text())   
            c = [0.0]*alpha
            for i in range(alpha):
                c[i] = float(self.dynamic_widgets[f"c-{i+1}"].text()) 
            A = [[0.0]*T]*m
            for i in range(m):
                for t in range(T):
                        A[i][t] = float(self.dynamic_widgets[f"d-{j+1}-{t+1}"].text())
            a = [[0.0]*n]*m
            for i in range(m):
                for j in range(n):
                        a[i][j] = float(self.dynamic_widgets[f"a-{i+1}-{j+1}"].text())
            R_fix = [[0.0]*T]*(m-alpha)
            for i in range(m-alpha):
                for t in range(T):
                        R_fix[i][t] = float(self.dynamic_widgets[f"R_fix-{i+1}-{t+1}"].text())
            x_a = [0.0]*n
            for j in range(n):
                x_a[j] = float(self.dynamic_widgets[f"x_a-{j+1}"].text()) 
            R_a = [0.0]*alpha
            for i in range(alpha):
                    R_a[i] = float(self.dynamic_widgets[f"Ra-{i+1}"].text())

        except ValueError:
                # Falls es einen Fehler gibt (keine gültige Zahl), zeige ein Fehler-Popup
                self.show_error_message(f"one of the entry is not valid. Please enter a valid number.")
                return  # Verhindere die Ausführung des Solvers, wenn Fehler aufgetreten ist
        self.params = params
        # Solver aufrufen und Ergebnisse speichern
        self.results  = run_gurobi_solver(n, m, alpha, T, x_a, R_a, R_fix, a, A, b, c, h, k, p , d, q)
      
        # Performance label update
        self.update_performance_label()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
