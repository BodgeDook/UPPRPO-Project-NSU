class RegisterView(QWidget):
    def __init__(self, switch_callback):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Register Page"))
        
        switch_button = QPushButton("Already have an account?")
        switch_button.clicked.connect(switch_callback)
        layout.addWidget(switch_button)

class LoginView(QWidget):
    def __init__(self, switch_callback):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Login Page"))
        
        switch_button = QPushButton("Don't have an account?")
        switch_button.clicked.connect(switch_callback)
        layout.addWidget(switch_button)

class AuthView(QWidget):
    def __init__(self, view_model):
        super().__init__()
        self.view_model = view_model
        self.layout = QVBoxLayout(self)
        self.stacked_widget = QStackedWidget()
        
        self.register_view = RegisterView(self.view_model.switch_to_login)
        self.login_view = LoginView(self.view_model.switch_to_register)
        
        self.stacked_widget.addWidget(self.register_view)
        self.stacked_widget.addWidget(self.login_view)

        self.layout.addWidget(self.stacked_widget)
        
        self.view_model.state_changed.connect(self.update_view)
        self.update_view()  # Set initial state

    def update_view(self):
        self.stacked_widget.setCurrentIndex(self.view_model.current_state)