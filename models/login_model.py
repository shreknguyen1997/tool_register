
import requests
from bs4 import BeautifulSoup
import re
import time

class LoginModel:
    def __init__(self, driver_path=None):
        # driver_path is kept for backward compatibility but not used
        self.session = requests.Session()
        # Set a user agent to mimic a browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def login(self, url, username, password):
        try:
            # Xử lý đặc biệt cho trang web hoclythuyetlaixe.eco-tek.com.vn
            if "hoclythuyetlaixe.eco-tek.com.vn" in url:
                return self.login_hoclythuyetlaixe(url ,username, password)

            # Xử lý mặc định cho các trang web khác
            # Đầu tiên, lấy trang đăng nhập để có thể lấy các token CSRF nếu cần
            response = self.session.get(url)

            # Phân tích HTML để tìm form đăng nhập
            soup = BeautifulSoup(response.text, 'html.parser')

            # Tìm form đăng nhập
            login_form = soup.find('form')

            if not login_form:
                print(f"Không tìm thấy form đăng nhập trên trang {url}")
                return False

            # Xác định action URL của form
            form_action = login_form.get('action')
            if form_action:
                if form_action.startswith('/'):
                    # Relative URL
                    login_url = url.split('//', 1)[0] + '//' + url.split('//', 1)[1].split('/', 1)[0] + form_action
                elif form_action.startswith('http'):
                    # Absolute URL
                    login_url = form_action
                else:
                    # Relative URL without leading slash
                    base_url = url.rstrip('/').rsplit('/', 1)[0]
                    login_url = f"{base_url}/{form_action}"
            else:
                # If no action, use the current URL
                login_url = url

            # Chuẩn bị dữ liệu đăng nhập
            login_data = {
                'username': username,
                'password': password
            }

            # Tìm các trường ẩn trong form (như CSRF token)
            hidden_inputs = login_form.find_all('input', {'type': 'hidden'})
            for hidden_input in hidden_inputs:
                name = hidden_input.get('name')
                value = hidden_input.get('value', '')
                if name:
                    login_data[name] = value

            # Gửi request đăng nhập
            login_response = self.session.post(login_url, data=login_data, allow_redirects=True)

            # Kiểm tra đăng nhập thành công
            # Thường sau khi đăng nhập thành công, người dùng sẽ được chuyển hướng đến trang dashboard
            # hoặc có thể kiểm tra một số text chỉ xuất hiện khi đăng nhập thành công
            if "dashboard" in login_response.url or "logout" in login_response.text.lower():
                print(f"Tài khoản {username} đăng nhập thành công!")
                return True
            else:
                print(f"Tài khoản {username} đăng nhập thất bại.")
                return False

        except Exception as e:
            print(f"Lỗi với tài khoản {username}: {e}")
            return False

    def login_hoclythuyetlaixe(self, url, username, password):
            # Mở trang web
            self.driver.get(url)

            # Tìm trường tên đăng nhập và mật khẩu, điền thông tin
            username_field = self.driver.find_element(By.NAME, "login")  # Thay "login" với tên trường thực tế
            password_field = self.driver.find_element(By.NAME, "password")  # Thay "password" với tên trường thực tế

            # Nhập thông tin đăng nhập
            username_field.send_keys(username)
            password_field.send_keys(password)

            # Tìm nút đăng nhập và nhấn
            login_button = self.driver.find_element(By.XPATH, '//button[@type="submit"]')  # Thay XPath với vị trí nút thực tế
            login_button.click()

            # Đợi trang phản hồi
            time.sleep(3)  # Đợi 3 giây để trang tải lại

            # Kiểm tra đăng nhập thành công bằng URL hoặc thông tin trên trang
            if "dashboard" in self.driver.current_url or "logout" in self.driver.page_source.lower():
                print(f"Tài khoản {username} đăng nhập thành công!")
                return True
            else:
                print(f"Tài khoản {username} đăng nhập thất bại.")
                return False
    def close(self):
        self.driver.quit()  # Đóng trình duyệt sau khi sử dụng
