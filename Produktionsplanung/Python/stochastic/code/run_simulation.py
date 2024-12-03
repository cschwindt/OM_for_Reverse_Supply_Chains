from PyQt5.QtWidgets import ( QApplication, QMainWindow, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget, 
                             QGridLayout, QSizePolicy,QDesktopWidget, QShortcut, QFileDialog, QMessageBox)
from PyQt5.QtGui import QFont, QPixmap , QKeySequence
from model_Sto_backend import *
from PyQt5.QtCore import Qt
import sys

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
            "T (periods)": 2, "n (products)": 1, "m (factors)": 2, "alpha ": 1, "q (samples)": 100
        }

        param_layout = QHBoxLayout()
        for param, default in self.params.items():
            label = QLabel(param)
            label.setFont(QFont("Georgia", 10, QFont.Bold))
            input_field = QLineEdit(str(default))
            self.param_inputs[param] = input_field
            param_layout.addWidget(label)
            param_layout.addWidget(input_field)
        
        submit_button = QPushButton("Generate Input Fields")
        submit_button.setFont(QFont("Arial", 10, QFont.Bold))
        submit_button.setStyleSheet("background-color: lightblue;")
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
        self.run_button = QPushButton("Run MPS_CE_Sampling")
        self.run_button.setFont(QFont("Arial", 10, QFont.Bold))
        self.run_button.setStyleSheet("background-color: lightgreen;")
        self.run_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.run_button.clicked.connect(self.run_solver)
        button_layout.addWidget(self.run_button)

        # Save Results Button
        self.save_button = QPushButton("Save Results as Excel File")
        self.save_button.setFont(QFont("Arial", 10, QFont.Bold))
        self.save_button.setStyleSheet("background-color: yellow;")
        self.save_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button_layout.addWidget(self.save_button)

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

    
    def generate_fields(self):
        # Clear previous dynamic widgets
        self.clear_layout(self.dynamic_layout)
       
        # Get values for T, n, m
        T = int(self.param_inputs["T (periods)"].text())
        n = int(self.param_inputs["n (products)"].text())
        m = int(self.param_inputs["m (factors)"].text())
        alpha = int(self.param_inputs["alpha "].text())
        
        label_widget = QLabel(f"d (Demand):")
        label_widget.setFont(QFont("Georgia", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, 0, 0)
        for j in range(n):
            for t in range(T):
                field = QLineEdit()
                self.dynamic_layout.addWidget(field, j, t + 1)  # Add fields next to the label
                self.dynamic_widgets[f"d-{j+1}-{t+1}"] = field
        
        label_widget = QLabel(f"p (Price):")
        label_widget.setFont(QFont("Georgia", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+1, 0)
        for j in range(n):
                field = QLineEdit()
                self.dynamic_layout.addWidget(field, n+1, j + 1)  # Add fields next to the label
                self.dynamic_widgets[f"p-{j+1}"] = field
        
        label_widget = QLabel(f"k (production cost):")
        label_widget.setFont(QFont("Georgia", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+2, 0)
        for j in range(n):
                field = QLineEdit()
                self.dynamic_layout.addWidget(field, n+2, j + 1)  # Add fields next to the label
                self.dynamic_widgets[f"k-{j+1}"] = field     

        label_widget = QLabel(f"h (holding cost):")
        label_widget.setFont(QFont("Georgia", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+3, 0)
        for j in range(n):
                field = QLineEdit()
                self.dynamic_layout.addWidget(field, n+3, j + 1)  # Add fields next to the label
                self.dynamic_widgets[f"h-{j+1}"] = field    
        
        label_widget = QLabel(f"A (avaibility):")
        label_widget.setFont(QFont("Georgia", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+4, 0)
        for i in range(m):
            for t in range(T):
                field = QLineEdit()
                self.dynamic_layout.addWidget(field, n+i+4, t + 1)  # Add fields next to the label
                self.dynamic_widgets[f"A-{i+1}-{t+1}"] = field   

        label_widget = QLabel(f"x_a (initial inventory products):")
        label_widget.setFont(QFont("Georgia", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+m+5, 0)
        for j in range(n):
                field = QLineEdit()
                self.dynamic_layout.addWidget(field, n+m+5, j + 1)  # Add fields next to the label
                self.dynamic_widgets[f"x_a-{j+1}"] = field   
        
        label_widget = QLabel(f"a (production coefficients):")
        label_widget.setFont(QFont("Georgia", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+m+6, 0)
        for i in range(m):
            for j in range(n):
                field = QLineEdit()
                self.dynamic_layout.addWidget(field, n+m+i+6, j + 1)  # Add fields next to the label
                self.dynamic_widgets[f"a-{i+1}-{j+1}"] = field
        
        label_widget = QLabel(f"R_a (initial inventory levels of secondary materials):")
        label_widget.setFont(QFont("Georgia", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+2*m+7, 0)
        for i in range(alpha):
                field = QLineEdit()
                self.dynamic_layout.addWidget(field, n+2*m+7, i + 1)
                self.dynamic_widgets[f"Ra-{i+1}"] = field
        
        label_widget = QLabel(f"b (procurement cost of secondary materials):")
        label_widget.setFont(QFont("Georgia", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+2*m+8, 0)
        for i in range(alpha):
                field = QLineEdit()
                self.dynamic_layout.addWidget(field, n+2*m+8, i + 1)
                self.dynamic_widgets[f"b-{i+1}"] = field
        
        label_widget = QLabel(f"c (procurement cost of corresponding primary materials):")
        label_widget.setFont(QFont("Georgia", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+2*m+9, 0)
        for i in range(alpha):
                field = QLineEdit()
                self.dynamic_layout.addWidget(field, n+2*m+9, i + 1)
                self.dynamic_widgets[f"c-{i+1}"] = field
        
        label_widget = QLabel(f"Rfix (capacity of non-secondary production factors):")
        label_widget.setFont(QFont("Georgia", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+2*m+10, 0)
        for i in range(m-alpha):
            for t in range(T):
                field = QLineEdit()
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
    
        self.params = params
        # Solver aufrufen und Ergebnisse speichern
        self.results  = run_gurobi_solver(params , self.dynamic_widgets)

        # Performance label update
        self.update_performance_label()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
