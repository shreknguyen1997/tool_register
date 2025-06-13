
class LoginController:
    def __init__(self, model, view):
        self.model = model
        self.view = view

    def handle_login(self, url, username, password):
        result = self.model.login(url, username, password)

        if not result:
            self.view.show_error("Login failed. Please check your credentials.")

        return result
