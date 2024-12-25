from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget, 
                             QGridLayout, QSizePolicy, QDesktopWidget, QShortcut, QFileDialog, QMessageBox)
from PyQt5.QtGui import QFont, QPixmap, QKeySequence
from backend_det import *
from PyQt5.QtCore import Qt
import sys
import json


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # determine screen size
        screen_geometry = QDesktopWidget().availableGeometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()

        # set window size to screen size
        self.resize(screen_width, screen_height)
        self.setWindowFlags(Qt.WindowShadeButtonHint)

        # main layout
        main_layout = QVBoxLayout()

        # horizontal header with logo and text
        header_layout = QHBoxLayout()

        # logo
        logo_label = QLabel()
        logo_pixmap = QPixmap("logo.png").scaled(60, 60, Qt.KeepAspectRatio)
        logo_label.setPixmap(logo_pixmap)
        header_layout.addWidget(logo_label, alignment=Qt.AlignLeft)
        
        # text
        title_label = QLabel("Operations Management Group\nInstitute of Management and Economics")
        title_label.setFont(QFont("Arial", 14, QFont.Normal))
        header_layout.addWidget(title_label, alignment=Qt.AlignLeft)

        header_layout.addStretch()

        main_layout.addLayout(header_layout)

        # input fields for T, n, m
        self.param_inputs = {}
        self.params = {
            "T (periods)": 12, "n (products)": 6, "m (factors)": 4, "m_A (secondary factors)": 2
        }

        param_layout = QHBoxLayout()
        for param, value in self.params.items():
            label = QLabel(param)
            label.setFont(QFont("Arial", 10, QFont.Bold))
            input_field = QLineEdit(str(value))
            input_field.setMaximumWidth(50)
            self.param_inputs[param] = input_field
            param_layout.addWidget(input_field)
            param_layout.addWidget(label)
            
        submit_button = QPushButton("Generate Input Fields")
        submit_button.setFont(QFont("Arial", 10, QFont.Bold))
        submit_button.setStyleSheet("background-color: lightgray;")
        submit_button.clicked.connect(self.generate_fields)
        param_layout.addWidget(submit_button)

        main_layout.addLayout(param_layout)

        # dynamic fields (demand, availability, etc.)
        self.dynamic_layout = QGridLayout()
        self.dynamic_widgets = {}

        main_layout.addLayout(self.dynamic_layout)

        # buttons (Run Solver and Save Results)
        button_layout = QHBoxLayout()

        # Run Solver button
        self.run_button = QPushButton("Run Solver")
        self.run_button.setFont(QFont("Arial", 10, QFont.Bold))
        self.run_button.setStyleSheet("background-color: lightgray;")
        self.run_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.run_button.clicked.connect(self.run_solver)
        button_layout.addWidget(self.run_button)

        # Save Results button
        self.save_button = QPushButton("Save Parameters")
        self.save_button.setFont(QFont("Arial", 10, QFont.Bold))
        self.save_button.setStyleSheet("background-color: lightgray;")
        self.save_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.save_button.clicked.connect(self.save_data)
        button_layout.addWidget(self.save_button)

        # Load Results button
        self.load_button = QPushButton("Load Parameters")
        self.load_button.setFont(QFont("Arial", 10, QFont.Bold))
        self.load_button.setStyleSheet("background-color: lightgray;")
        self.load_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.load_button.clicked.connect(self.load_data)
        button_layout.addWidget(self.load_button)

        main_layout.addLayout(button_layout)

        # results
        self.results = None
        self.results_layout = QVBoxLayout()
        self.results_label = QLabel("")
        self.results_layout.addWidget(self.results_label)

        main_layout.addLayout(self.results_layout)

        # set up the main window layout
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # generate default fields
        self.generate_fields()

        # add a shortcut to close the window (Ctrl+Q)
        close_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
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
        T = int(self.params["T (periods)"])   # number of periods
        n = int(self.params["n (products)"])  # number of products
        m = int(self.params["m (factors)"])   # number of production factors
        m_A = int(self.params["m_A (secondary factors)"])
        I_A = range(m_A)

        d = [[0.0] * T for _ in range(n)]
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
        b = [0.0]*m_A
        for i in range(m_A):
            b[i] = float(self.dynamic_widgets[f"b-{i+1}"].text())   
        c = [0.0]*m_A
        for i in range(m_A):
            c[i] = float(self.dynamic_widgets[f"c-{i+1}"].text()) 
        A = [[0.0] * T for _ in range(m_A)]
        for i in range(m_A):
            for t in range(T):
                A[i][t] = float(self.dynamic_widgets[f"A-{i+1}-{t+1}"].text())
        a = [[0.0] * n for _ in range(m)]
        for i in range(m):
            for j in range(n):
                a[i][j] = float(self.dynamic_widgets[f"a-{i+1}-{j+1}"].text())
        I_minus_I_A = [i for i in range(m) if i not in I_A]  
        R_fix = [[0.0] * T for _ in range(m-m_A)]
        for i in range(m-m_A):
            for t in range(T):
                R_fix[i][t] = float(self.dynamic_widgets[f"R_fix-{i+1}-{t+1}"].text())
        x_a = [0.0]*n
        for j in range(n):
            x_a[j] = float(self.dynamic_widgets[f"x_a-{j+1}"].text())
        R_a = [0.0]*m_A
        for i in range(m_A):
            R_a[i] = float(self.dynamic_widgets[f"Ra-{i+1}"].text())
        
        data_to_save = {
            "T": T,
            "n": n,
            "m": m,
            "m_A": m_A,
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
        # choose an existing json file
        file_path, _ = QFileDialog.getSaveFileName(self, "save parameters as json-file", "", "json-file (*.json)")

        if not file_path:
            return

        with open(f"{file_path}", "w") as file:
            json.dump(data_to_save, file, indent=4)

    def load_data(self):

        # choose an existing json file
        file_path, _ = QFileDialog.getOpenFileName(self, "select a json-file with saved parameters ", "",
                                                   "json-file (*.json)")

        if not file_path:
            return

        with open(f"{file_path}", "r") as file:
            loaded_data = json.load(file)
    
        # clear previous dynamic widgets
        self.clear_layout(self.dynamic_layout)
       
        self.params["T (periods)"] = loaded_data["T"]
        self.params["n (products)"] = loaded_data["n"]
        self.params["m (factors)"] = loaded_data["m"]
        self.params["m_A (secondary factors)"] = loaded_data["m_A"]

        self.param_inputs["T (periods)"].setText(str(self.params["T (periods)"]))
        self.param_inputs["n (products)"].setText(str(self.params["n (products)"]))
        self.param_inputs["m (factors)"].setText(str(self.params["m (factors)"]))
        self.param_inputs["m_A (secondary factors)"].setText(str(self.params["m_A (secondary factors)"]))
        
        T = self.params["T (periods)"]
        n = self.params["n (products)"]
        m = self.params["m (factors)"]
        m_A = self.params["m_A (secondary factors)"]
        
        label_widget = QLabel(f"d (demands):")
        label_widget.setFont(QFont("Arial", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, 0, 0)
        for j in range(n):
            for t in range(T):
                field = QLineEdit(str(loaded_data["d"][j][t]))
                field.setCursorPosition(0)
                field.setMaximumWidth(50)
                self.dynamic_layout.addWidget(field, j, t + 1)  # add fields next to the label
                self.dynamic_widgets[f"d-{j+1}-{t+1}"] = field
        
        label_widget = QLabel(f"p (prices):")
        label_widget.setFont(QFont("Arial", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+1, 0)
        for j in range(n):
            field = QLineEdit(str(loaded_data["p"][j]))
            field.setCursorPosition(0)
            field.setMaximumWidth(50)
            self.dynamic_layout.addWidget(field, n+1, j + 1)  # add fields next to the label
            self.dynamic_widgets[f"p-{j+1}"] = field
        
        label_widget = QLabel(f"k (production costs):")
        label_widget.setFont(QFont("Arial", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+2, 0)
        for j in range(n):
            field = QLineEdit(str(loaded_data["k"][j]))
            field.setCursorPosition(0)
            field.setMaximumWidth(50)
            self.dynamic_layout.addWidget(field, n+2, j + 1)  # add fields next to the label
            self.dynamic_widgets[f"k-{j+1}"] = field
        
        label_widget = QLabel(f"h (holding costs):")
        label_widget.setFont(QFont("Arial", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+3, 0)
        for j in range(n):
            field = QLineEdit(str(loaded_data["h"][j]))
            field.setCursorPosition(0)
            field.setMaximumWidth(50)
            self.dynamic_layout.addWidget(field, n+3, j + 1)  # add fields next to the label
            self.dynamic_widgets[f"h-{j+1}"] = field
        
        label_widget = QLabel(f"A (availabilities of secondary materials):")
        label_widget.setFont(QFont("Arial", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+4, 0)
        for i in range(m_A):
            for t in range(T):
                field = QLineEdit(str(loaded_data["A"][i][t]))
                field.setCursorPosition(0)
                field.setMaximumWidth(50)
                self.dynamic_layout.addWidget(field, n+i+4, t + 1)  # add fields next to the label
                self.dynamic_widgets[f"A-{i+1}-{t+1}"] = field   

        label_widget = QLabel(f"x_a (initial inventory levels of products):")
        label_widget.setFont(QFont("Arial", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+m+5, 0)
        for j in range(n):
            field = QLineEdit(str(loaded_data["x_a"][j]))
            field.setCursorPosition(0)
            field.setMaximumWidth(50)
            self.dynamic_layout.addWidget(field, n+m+5, j + 1)  # add fields next to the label
            self.dynamic_widgets[f"x_a-{j+1}"] = field
        
        label_widget = QLabel(f"a (production coefficients):")
        label_widget.setFont(QFont("Arial", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+m+6, 0)
        for i in range(m):
            for j in range(n):
                field = QLineEdit(str(loaded_data["a"][i][j]))
                field.setCursorPosition(0)
                field.setMaximumWidth(50)
                self.dynamic_layout.addWidget(field, n+m+i+6, j + 1)  # add fields next to the label
                self.dynamic_widgets[f"a-{i+1}-{j+1}"] = field
        
        label_widget = QLabel(f"R_a (initial inventory levels of secondary materials):")
        label_widget.setFont(QFont("Arial", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+2*m+7, 0)
        for i in range(m_A):
            field = QLineEdit(str(loaded_data["R_a"][i]))
            field.setCursorPosition(0)
            field.setMaximumWidth(50)
            self.dynamic_layout.addWidget(field, n+2*m+7, i + 1)
            self.dynamic_widgets[f"Ra-{i+1}"] = field
        
        label_widget = QLabel(f"b (procurement costs of secondary materials):")
        label_widget.setFont(QFont("Arial", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+2*m+8, 0)
        for i in range(m_A):
            field = QLineEdit(str(loaded_data["b"][i]))
            field.setCursorPosition(0)
            field.setMaximumWidth(50)
            self.dynamic_layout.addWidget(field, n+2*m+8, i + 1)
            self.dynamic_widgets[f"b-{i+1}"] = field
        
        label_widget = QLabel(f"c (procurement costs of corresponding primary materials):")
        label_widget.setFont(QFont("Arial", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+2*m+9, 0)
        for i in range(m_A):
            field = QLineEdit(str(loaded_data["c"][i]))
            field.setCursorPosition(0)
            field.setMaximumWidth(50)
            self.dynamic_layout.addWidget(field, n+2*m+9, i + 1)
            self.dynamic_widgets[f"c-{i+1}"] = field
        
        label_widget = QLabel(f"Rfix (capacities of non-secondary production factors):")
        label_widget.setFont(QFont("Arial", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+2*m+10, 0)
        for i in range(m-m_A):
            for t in range(T):
                field = QLineEdit(str(loaded_data["R_fix"][i][t]))
                field.setCursorPosition(0)
                field.setMaximumWidth(50)
                self.dynamic_layout.addWidget(field, n+2*m+10+i, t + 1)
                self.dynamic_widgets[f"R_fix-{i+1}-{t+1}"] = field
        
    def generate_fields(self):
        # clear previous dynamic widgets
        self.clear_layout(self.dynamic_layout)
       
        # get values for T, n, m, m_A
        T = int(self.param_inputs["T (periods)"].text())
        n = int(self.param_inputs["n (products)"].text())
        m = int(self.param_inputs["m (factors)"].text())
        m_A = int(self.param_inputs["m_A (secondary factors)"].text())
        
        label_widget = QLabel(f"d (demands)")
        label_widget.setFont(QFont("Arial", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, 0, 0)
        for j in range(n):
            for t in range(T):
                field = QLineEdit()
                field.setMaximumWidth(50)
                self.dynamic_layout.addWidget(field, j, t + 1)  # add fields next to the label
                self.dynamic_widgets[f"d-{j+1}-{t+1}"] = field
        
        label_widget = QLabel(f"p (prices)")
        label_widget.setFont(QFont("Arial", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+1, 0)
        for j in range(n):
            field = QLineEdit()
            field.setMaximumWidth(50)
            self.dynamic_layout.addWidget(field, n+1, j + 1)  # add fields next to the label
            self.dynamic_widgets[f"p-{j+1}"] = field
        
        label_widget = QLabel(f"k (production costs)")
        label_widget.setFont(QFont("Arial", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+2, 0)
        for j in range(n):
            field = QLineEdit()
            field.setMaximumWidth(50)
            self.dynamic_layout.addWidget(field, n+2, j + 1)  # add fields next to the label
            self.dynamic_widgets[f"k-{j+1}"] = field

        label_widget = QLabel(f"h (holding costs)")
        label_widget.setFont(QFont("Arial", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+3, 0)
        for j in range(n):
            field = QLineEdit()
            field.setMaximumWidth(50)
            self.dynamic_layout.addWidget(field, n+3, j + 1)  # add fields next to the label
            self.dynamic_widgets[f"h-{j+1}"] = field
        
        label_widget = QLabel(f"A (availabilities of secondary materials)")
        label_widget.setFont(QFont("Arial", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+4, 0)
        for i in range(m_A):
            for t in range(T):
                field = QLineEdit()
                field.setMaximumWidth(50)
                self.dynamic_layout.addWidget(field, n+i+4, t + 1)  # add fields next to the label
                self.dynamic_widgets[f"A-{i+1}-{t+1}"] = field   

        label_widget = QLabel(f"x_a (initial inventory levels of products)")
        label_widget.setFont(QFont("Arial", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+m+5, 0)
        for j in range(n):
            field = QLineEdit()
            field.setMaximumWidth(50)
            self.dynamic_layout.addWidget(field, n+m+5, j + 1)  # add fields next to the label
            self.dynamic_widgets[f"x_a-{j+1}"] = field
        
        label_widget = QLabel(f"a (production coefficients)")
        label_widget.setFont(QFont("Arial", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+m+6, 0)
        for i in range(m):
            for j in range(n):
                field = QLineEdit()
                field.setMaximumWidth(50)
                self.dynamic_layout.addWidget(field, n+m+i+6, j + 1)  # add fields next to the label
                self.dynamic_widgets[f"a-{i+1}-{j+1}"] = field
        
        label_widget = QLabel(f"R_a (initial inventory levels of secondary materials)")
        label_widget.setFont(QFont("Arial", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+2*m+7, 0)
        for i in range(m_A):
            field = QLineEdit()
            field.setMaximumWidth(50)
            self.dynamic_layout.addWidget(field, n+2*m+7, i + 1)
            self.dynamic_widgets[f"Ra-{i+1}"] = field
        
        label_widget = QLabel(f"b (procurement costs of secondary materials)")
        label_widget.setFont(QFont("Arial", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+2*m+8, 0)
        for i in range(m_A):
            field = QLineEdit()
            field.setMaximumWidth(50)
            self.dynamic_layout.addWidget(field, n+2*m+8, i + 1)
            self.dynamic_widgets[f"b-{i+1}"] = field
        
        label_widget = QLabel(f"c (procurement costs of corresponding primary materials)")
        label_widget.setFont(QFont("Arial", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+2*m+9, 0)
        for i in range(m_A):
            field = QLineEdit()
            field.setMaximumWidth(50)
            self.dynamic_layout.addWidget(field, n+2*m+9, i + 1)
            self.dynamic_widgets[f"c-{i+1}"] = field
        
        label_widget = QLabel(f"Rfix (capacities of non-secondary production factors)")
        label_widget.setFont(QFont("Arial", 10, QFont.Bold))
        self.dynamic_layout.addWidget(label_widget, n+2*m+10, 0)
        for i in range(m-m_A):
            for t in range(T):
                field = QLineEdit()
                field.setMaximumWidth(50)
                self.dynamic_layout.addWidget(field, n+2*m+10+i, t + 1)
                self.dynamic_widgets[f"R_fix-{i+1}-{t+1}"] = field
    
    def show_error_message(self, message):
        # show an error message
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setText(message)
        msg_box.setWindowTitle("Error")
        msg_box.exec_()    

    def run_solver(self):
        # try to convert all parameter values
        params = {}
        for key, input_field in self.param_inputs.items():
            try:
                # try to convert the text to a number
                params[key] = float(input_field.text())

                # check if value is negative
                if params[key] < 0:
                    self.show_error_message(f"The entry for '{key}' cannot be negative. Please enter a valid number.")
                    return  # prevent the execution of the solver if the value is negative
           
            except ValueError:
                # show an error message if there is an error
                self.show_error_message(f"The entry for '{key}' is not valid. Please enter a valid number.")
                return  # prevent the execution of the solver if an error occurred
        
        T = int(params["T (periods)"])   # number of periods
        n = int(params["n (products)"])  # number of products
        m = int(params["m (factors)"])   # number of production factors
        m_A = int(params["m_A (secondary factors)"])

        try:
            d = [[0.0] * T for _ in range(n)]
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
            b = [0.0]*m_A
            for i in range(m_A):
                b[i] = float(self.dynamic_widgets[f"b-{i+1}"].text())   
            c = [0.0]*m_A
            for i in range(m_A):
                c[i] = float(self.dynamic_widgets[f"c-{i+1}"].text())
            A = [[0.0] * T for _ in range(m_A)]
            for i in range(m_A):
                for t in range(T):
                    A[i][t] = float(self.dynamic_widgets[f"A-{i+1}-{t+1}"].text())
            a = [[0.0] * n for _ in range(m)]
            for i in range(m):
                for j in range(n):
                    a[i][j] = float(self.dynamic_widgets[f"a-{i+1}-{j+1}"].text())
            R_fix = [[0.0] * T for _ in range(m-m_A)]
            for i in range(m-m_A):
                for t in range(T):
                    R_fix[i][t] = float(self.dynamic_widgets[f"R_fix-{i+1}-{t+1}"].text())
            x_a = [0.0]*n
            for j in range(n):
                x_a[j] = float(self.dynamic_widgets[f"x_a-{j+1}"].text()) 
            R_a = [0.0]*m_A
            for i in range(m_A):
                R_a[i] = float(self.dynamic_widgets[f"Ra-{i+1}"].text())

        except ValueError:
            # show an error message if some entry is invalid
            self.show_error_message(f"One of the entries is invalid. Please enter a valid number.")
            return  # prevent execution of solver if error occurred
        self.params = params
        # execute the solver and save the results
        self.results = run_gurobi_solver(n, m, m_A, T, x_a, R_a, R_fix, a, A, b, c, h, k, p, d)
      
        # update the performance label
        self.update_performance_label()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
