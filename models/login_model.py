from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

class LoginModel:
    def __init__(self, driver_path):
        """
        Khởi tạo model với đường dẫn đến ChromeDriver.
        :param driver_path: Đường dẫn đến ChromeDriver (Cần phải cung cấp)
        """
        self.driver_path = driver_path
        # Lưu trữ các driver instances cho mỗi user
        self.drivers = {}
        print("LoginModel đã được khởi tạo.")

    def login(self, url, username, password):
        """
        Hàm đăng nhập chính, sử dụng Selenium để tự động mở trình duyệt, điền thông tin và nhấn nút đăng nhập.

        :param url: URL của trang đăng nhập.
        :param username: Tên đăng nhập.
        :param password: Mật khẩu.
        :return: True nếu đăng nhập thành công, False nếu thất bại.
        """
        try:
            # Tạo một driver mới cho user này
            service = Service(self.driver_path)
            chrome_options = Options()
            # Có thể thêm các options khác nếu cần
            # chrome_options.add_argument("--headless")  # Chạy ẩn (không hiển thị giao diện)

            # Khởi tạo ChromeDriver mới
            driver = webdriver.Chrome()
            # Lưu driver vào dictionary với key là username
            self.drivers[username] = driver

            # Mở trình duyệt và truy cập vào URL đăng nhập
            print(f"Đang mở trình duyệt mới cho {username} và truy cập {url}...")
            driver.get(url)
            time.sleep(3)  # Đợi 3 giây để trang tải hoàn toàn

            # Tìm trường tên đăng nhập bằng nhiều cách khác nhau
            print("Đang tìm trường nhập tên đăng nhập...")
            username_field = None

            # Danh sách các thuộc tính có thể dùng để tìm trường username
            username_identifiers = [
                (By.ID, "username"), 
                (By.ID, "email"),
                (By.ID, "login"),
                (By.ID, "user"),
                (By.ID, "userid"),
                (By.NAME, "username"),
                (By.NAME, "email"),
                (By.NAME, "login"),
                (By.NAME, "user"),
                (By.XPATH, "//input[@type='text']"),
                (By.XPATH, "//input[@type='email']"),
                (By.XPATH, "//input[contains(@placeholder, 'user')]"),
                (By.XPATH, "//input[contains(@placeholder, 'email')]"),
                (By.XPATH, "//input[contains(@placeholder, 'login')]"),
                (By.XPATH, "//input[contains(@class, 'user')]"),
                (By.XPATH, "//input[contains(@class, 'email')]"),
                (By.XPATH, "//input[contains(@class, 'login')]")
            ]

            # Thử từng cách để tìm trường username
            for by_method, identifier in username_identifiers:
                try:
                    username_field = driver.find_element(by_method, identifier)
                    print(f"Đã tìm thấy trường username với {by_method}: {identifier}")
                    break
                except:
                    continue

            # Nếu không tìm thấy, thử lấy tất cả các input và chọn cái đầu tiên
            if username_field is None:
                print("Không tìm thấy trường username bằng các cách thông thường, thử phương pháp khác...")
                input_fields = driver.find_elements(By.XPATH, "//input")
                if input_fields:
                    username_field = input_fields[0]
                    print("Đã chọn trường input đầu tiên làm trường username")

            # Nếu vẫn không tìm thấy, báo lỗi
            if username_field is None:
                raise Exception("Không thể tìm thấy trường nhập tên đăng nhập")

            # Tìm trường mật khẩu bằng nhiều cách khác nhau
            print("Đang tìm trường nhập mật khẩu...")
            password_field = None

            # Danh sách các thuộc tính có thể dùng để tìm trường password
            password_identifiers = [
                (By.ID, "password"),
                (By.ID, "pass"),
                (By.ID, "pwd"),
                (By.NAME, "password"),
                (By.NAME, "pass"),
                (By.NAME, "pwd"),
                (By.XPATH, "//input[@type='password']"),
                (By.XPATH, "//input[contains(@placeholder, 'password')]"),
                (By.XPATH, "//input[contains(@placeholder, 'pass')]"),
                (By.XPATH, "//input[contains(@class, 'password')]"),
                (By.XPATH, "//input[contains(@class, 'pass')]")
            ]

            # Thử từng cách để tìm trường password
            for by_method, identifier in password_identifiers:
                try:
                    password_field = driver.find_element(by_method, identifier)
                    print(f"Đã tìm thấy trường password với {by_method}: {identifier}")
                    break
                except:
                    continue

            # Nếu không tìm thấy, thử lấy tất cả các input type=password
            if password_field is None:
                print("Không tìm thấy trường password bằng các cách thông thường, thử phương pháp khác...")
                password_fields = driver.find_elements(By.XPATH, "//input[@type='password']")
                if password_fields:
                    password_field = password_fields[0]
                    print("Đã chọn trường input type=password đầu tiên")

            # Nếu vẫn không tìm thấy, báo lỗi
            if password_field is None:
                raise Exception("Không thể tìm thấy trường nhập mật khẩu")

            # Điền thông tin đăng nhập
            print(f"Đang điền thông tin đăng nhập cho tài khoản {username}...")
            username_field.clear()
            username_field.send_keys(username)
            time.sleep(1)  # Đợi một chút giữa các thao tác

            password_field.clear()
            password_field.send_keys(password)
            time.sleep(1)  # Đợi một chút giữa các thao tác

            # Tìm nút đăng nhập bằng nhiều cách khác nhau
            print("Đang tìm nút đăng nhập...")
            login_button = None

            # Danh sách các thuộc tính có thể dùng để tìm nút đăng nhập
            login_button_identifiers = [
                (By.XPATH, "//button[@type='submit']"),
                (By.XPATH, "//input[@type='submit']"),
                (By.XPATH, "//button[contains(text(), 'Login')]"),
                (By.XPATH, "//button[contains(text(), 'Sign in')]"),
                (By.XPATH, "//button[contains(text(), 'Đăng nhập')]"),
                (By.XPATH, "//input[contains(@value, 'Login')]"),
                (By.XPATH, "//input[contains(@value, 'Sign in')]"),
                (By.XPATH, "//input[contains(@value, 'Đăng nhập')]"),
                (By.XPATH, "//a[contains(text(), 'Login')]"),
                (By.XPATH, "//a[contains(text(), 'Sign in')]"),
                (By.XPATH, "//a[contains(text(), 'Đăng nhập')]"),
                (By.ID, "login-button"),
                (By.ID, "loginButton"),
                (By.ID, "signin-button"),
                (By.ID, "signinButton"),
                (By.CLASS_NAME, "login-button"),
                (By.CLASS_NAME, "loginButton"),
                (By.CLASS_NAME, "signin-button"),
                (By.CLASS_NAME, "signinButton")
            ]

            # Thử từng cách để tìm nút đăng nhập
            for by_method, identifier in login_button_identifiers:
                try:
                    login_button = driver.find_element(by_method, identifier)
                    print(f"Đã tìm thấy nút đăng nhập với {by_method}: {identifier}")
                    break
                except:
                    continue

            # Nếu không tìm thấy, thử nhấn Enter ở trường password
            if login_button is None:
                print("Không tìm thấy nút đăng nhập, thử nhấn Enter ở trường password...")
                password_field.send_keys(Keys.RETURN)
            else:
                # Nhấn nút đăng nhập
                print("Đang nhấn nút đăng nhập...")
                login_button.click()

            # Đợi trang phản hồi sau khi nhấn nút
            print("Đang đợi trang phản hồi...")
            time.sleep(5)  # Đợi lâu hơn để đảm bảo trang đã tải xong

            # Kiểm tra đăng nhập thành công bằng nhiều cách
            print("Đang kiểm tra kết quả đăng nhập...")
            success_indicators = [
                "dashboard" in driver.current_url,
                "account" in driver.current_url,
                "profile" in driver.current_url,
                "home" in driver.current_url,
                "logout" in driver.page_source.lower(),
                "sign out" in driver.page_source.lower(),
                "đăng xuất" in driver.page_source.lower(),
                username in driver.page_source
            ]

            if any(success_indicators):
                print(f"Tài khoản {username} đăng nhập thành công!")
                return True
            else:
                print(f"Tài khoản {username} đăng nhập thất bại.")
                return False

        except Exception as e:
            print(f"Lỗi khi đăng nhập với tài khoản {username}: {e}")
            # Chụp ảnh màn hình khi gặp lỗi để debug
            try:
                screenshot_path = f"error_screenshot_{username}_{int(time.time())}.png"
                driver.save_screenshot(screenshot_path)
                print(f"Đã lưu ảnh màn hình lỗi tại: {screenshot_path}")
            except:
                print("Không thể lưu ảnh màn hình lỗi")
            return False

    def close_driver(self, username):
        """Đóng trình duyệt cụ thể của một user."""
        if username in self.drivers:
            try:
                self.drivers[username].quit()
                print(f"Đã đóng trình duyệt của user {username}")
                del self.drivers[username]
            except Exception as e:
                print(f"Lỗi khi đóng trình duyệt của user {username}: {e}")

    def close_all_drivers(self):
        """Đóng tất cả các trình duyệt."""
        for username, driver in list(self.drivers.items()):
            try:
                driver.quit()
                print(f"Đã đóng trình duyệt của user {username}")
            except Exception as e:
                print(f"Lỗi khi đóng trình duyệt của user {username}: {e}")
        self.drivers.clear()

    def close(self):
        """Đóng tất cả trình duyệt sau khi sử dụng."""
        self.close_all_drivers()  # Đóng tất cả trình duyệt Selenium khi hoàn tất
