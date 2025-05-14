from PyQt5.QtCore import QObject
from models.auth import AuthModel, AuthWorker
from views.auth import AuthDialog

class AuthController(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._workers = []
        self.model = AuthModel()
        self.dialog= AuthDialog()

        # Hook up view → controller methods
        rv = self.dialog.register_view
        rv.register_requested.connect(self._on_register)

        lv = self.dialog.login_view
        lv.login_requested.connect(self._on_login)

    def exec_(self):
        # show the dialog modally and return its result code
        return self.dialog.exec_()

    def _on_register(self, email, pwd1, pwd2):
        # (re-use your existing checks or add new ones here)
        if pwd1 != pwd2:
            self.dialog.register_view.show_message("Passwords don’t match")
            return

        self._run_worker(email, pwd1, action="register",
                         on_result=lambda ok, data: self._handle_result(ok, data, stage="register"))

    def _on_login(self, email, password):
        self._run_worker(email, password, action="login",
                         on_result=lambda ok, data: self._handle_result(ok, data, stage="login"))

    def _run_worker(self, email, password, action, on_result):
        # Create and retain a reference so the thread isn’t garbage-collected
        worker = AuthWorker(self.model, email, password, action)
        self._workers.append(worker)

        # When the worker finishes, remove it from our list and delete it cleanly
        worker.finished.connect(worker.deleteLater)
        worker.finished.connect(lambda w=worker: self._workers.remove(w))

        # Connect result and start
        worker.result.connect(on_result)
        worker.start()

    def _handle_result(self, status_code, response, stage):
        view = (self.dialog.register_view
                if stage=="register" else self.dialog.login_view)

        if status_code == 200:
            # Success: close dialog with Accepted
            self.dialog.accept()
        else:
            # Show error message from the response
            view.show_message(response.get("detail", str(response)))