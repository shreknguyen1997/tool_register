import os
import sys
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
        self.driver_path = {}
        # Lưu trữ các driver instances cho mỗi user
        self.drivers = {}
        print("LoginModel đã được khởi tạo.")

    def get_chromedriver_path(self):
        if getattr(sys, 'frozen', False):
            # Nếu ứng dụng được đóng gói (ví dụ với PyInstaller), sử dụng _MEIPASS
            base_path = sys._MEIPASS
        else:
            # Nếu không, lấy đường dẫn thư mục của file hiện tại
            base_path = os.path.dirname(os.path.abspath(__file__))
            base_path = os.path.dirname(base_path)  # Đi lên 1 cấp để đến thư mục gốc của dự án

            # Đảm bảo chromedriver có trong thư mục 'drivers'
        chromedriver_path = os.path.join(base_path, "chromedriver", "chromedriver")

        print('chromedriver_path', chromedriver_path)
        return chromedriver_path

    def login(self, url, username, password):
        """
        Hàm đăng nhập chính, sử dụng Selenium để tự động mở trình duyệt, điền thông tin và nhấn nút đăng nhập.

        :param url: URL của trang đăng nhập.
        :param username: Tên đăng nhập.
        :param password: Mật khẩu.
        :return: True nếu đăng nhập thành công, False nếu thất bại.
        """
        try:
            print(f"{self.driver_path}")
            # Tạo một driver mới cho user này
            chrome_options = Options()
            # Add stability options
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--no-sandbox")
            # Enable DevTools for network monitoring
            chrome_options.add_argument("--remote-debugging-port=9222")  # Enable remote debugging
            chrome_options.add_argument("--auto-open-devtools-for-tabs")  # Automatically open DevTools
            # Có thể thêm các options khác nếu cần
            # chrome_options.add_argument("--headless")  # Chạy ẩn (không hiển thị giao diện)
            self.driver_path = self.get_chromedriver_path()
            # Khởi tạo Service với chromedriver path
            self.service = Service(self.driver_path)

            print(f"Service{self.service}")
            self.driver = webdriver.Chrome(service=self.service, options=chrome_options)
            print("webdriver",webdriver)
            self.driver.execute_cdp_cmd('Network.enable', {})

            # Khởi tạo ChromeDriver mới
            try:
                # On Windows, try initializing without service parameter first
                import os  # Make sure os is imported in this scope
                if os.name == 'nt':
                    print("Windows detected, trying to initialize ChromeDriver without service parameter first...")
                    try:
                        # No need to add these options again
                        # They are already added at the beginning of the function

                        driver = webdriver.Chrome(options=chrome_options)
                        print("ChromeDriver initialized successfully without service parameter!")
                        # Lưu driver vào dictionary với key là username
                        self.drivers[username] = driver
                    except Exception as e_no_service:
                        print(f"Error initializing ChromeDriver without service parameter: {e_no_service}")
                        print("Falling back to service parameter approach...")

                        # Try with service parameter as fallback
                        # First check if the path already has .exe extension
                        if not self.driver_path.endswith('.exe'):
                            driver_path_with_exe = self.driver_path + '.exe'
                            if os.path.exists(driver_path_with_exe):
                                service = Service(driver_path_with_exe)
                                print(f"Using Windows ChromeDriver: {driver_path_with_exe}")
                            else:
                                # Check if there's a chromedriver.exe in the same directory
                                driver_dir = os.path.dirname(self.driver_path)
                                driver_name = "chromedriver.exe"
                                alternative_path = os.path.join(driver_dir, driver_name)
                                if os.path.exists(alternative_path):
                                    service = Service(alternative_path)
                                    print(f"Using alternative ChromeDriver path: {alternative_path}")
                                else:
                                    print(f"Warning: ChromeDriver with .exe extension not found at {driver_path_with_exe}")
                                    print(f"Trying to use the original path: {self.driver_path}")
                        else:
                            # Path already has .exe extension
                            print(f"Using provided ChromeDriver path with .exe: {self.driver_path}")

                        # No need to add these options again
                        # They are already added at the beginning of the function

                        driver = webdriver.Chrome(service=service, options=chrome_options)
                        # Lưu driver vào dictionary với key là username
                        self.drivers[username] = driver
                else:
                    # For non-Windows systems, use the service parameter approach
                    # No need to add these options again
                    # They are already added at the beginning of the function

                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    # Lưu driver vào dictionary với key là username
                    self.drivers[username] = driver
            except Exception as e:
                print(f"Error initializing ChromeDriver: {e}")
                print("Trying to initialize ChromeDriver without service parameter as last resort...")
                try:
                    driver = webdriver.Chrome(options=chrome_options)
                    self.drivers[username] = driver
                except Exception as e2:
                    print(f"Error initializing ChromeDriver without service parameter: {e2}")
                    print(f"Please make sure ChromeDriver is installed and compatible with your Chrome browser version.")
                    print(f"You can download ChromeDriver from: https://chromedriver.chromium.org/downloads")
                    raise

            # Mở trình duyệt và truy cập vào URL đăng nhập
            print(f"Đang mở trình duyệt mới cho {username} và truy cập {url}...")
            driver.get(url)
            time.sleep(3)  # Đợi 3 giây để trang tải hoàn toàn

            # Check for CSRF token and other hidden fields
            print("Đang kiểm tra CSRF token và các trường ẩn khác...")
            try:
                # Find all hidden inputs
                hidden_inputs = driver.find_elements(By.XPATH, "//input[@type='hidden']")
                csrf_token = None
                redirect_field = None

                for hidden_input in hidden_inputs:
                    input_name = hidden_input.get_attribute('name')
                    input_value = hidden_input.get_attribute('value')
                    print(f"Trường ẩn: {input_name} = {input_value}")

                    if input_name == 'csrf_token':
                        csrf_token = input_value
                        print(f"Đã tìm thấy CSRF token: {csrf_token}")
                    elif input_name == 'redirect':
                        redirect_field = input_value
                        print(f"Đã tìm thấy trường redirect: {redirect_field}")
            except Exception as e:
                print(f"Lỗi khi kiểm tra CSRF token: {e}")

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
            if password:  # Chỉ điền mật khẩu nếu có
                password_field.send_keys(password)
                print("Đã điền mật khẩu")
            else:
                print("Mật khẩu trống, không điền gì")
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
            time.sleep(10)  # Đợi lâu hơn để đảm bảo trang đã tải xong

            # Kiểm tra xem có bị chuyển hướng về trang login không (có thể do CSRF token không hợp lệ)
            if "login" in driver.current_url.lower():
                print("Vẫn ở trang login, có thể do CSRF token không hợp lệ. Thử lại với JavaScript...")
                try:
                    # Tìm form đăng nhập
                    login_form = driver.find_element(By.TAG_NAME, "form")
                    form_action = login_form.get_attribute("action")
                    form_method = login_form.get_attribute("method")
                    print(f"Form action: {form_action}, method: {form_method}")

                    # Tìm tất cả các input trong form
                    inputs = login_form.find_elements(By.TAG_NAME, "input")
                    form_data = {}

                    for input_field in inputs:
                        input_name = input_field.get_attribute("name")
                        input_value = input_field.get_attribute("value")
                        if input_name:
                            form_data[input_name] = input_value

                    # Cập nhật giá trị username và password
                    if "login" in form_data:
                        form_data["login"] = username
                    if "password" in form_data:
                        form_data["password"] = password

                    print(f"Form data: {form_data}")

                    # Tạo JavaScript để submit form
                    js_code = """
                    var form = document.querySelector('form');
                    """

                    for name, value in form_data.items():
                        js_code += f"""
                        var input = form.querySelector('[name="{name}"]');
                        if (input) {{
                            input.value = "{value}";
                        }}
                        """

                    js_code += """
                    form.submit();
                    """

                    # Thực thi JavaScript
                    print("Đang submit form bằng JavaScript...")
                    driver.execute_script(js_code)

                    # Đợi trang phản hồi sau khi submit
                    print("Đang đợi trang phản hồi sau khi submit bằng JavaScript...")
                    time.sleep(10)  # Đợi lâu hơn để đảm bảo trang đã tải xong
                except Exception as e:
                    print(f"Lỗi khi thử submit form bằng JavaScript: {e}")
                    # Nếu JavaScript không hoạt động, thử phương pháp khác
                    try:
                        # Refresh trang để lấy CSRF token mới
                        print("Đang refresh trang để lấy CSRF token mới...")
                        driver.refresh()
                        time.sleep(5)

                        # Tìm lại các trường input
                        username_field = driver.find_element(By.ID, "login")
                        password_field = driver.find_element(By.ID, "password")

                        # Điền lại thông tin
                        username_field.clear()
                        username_field.send_keys(username)
                        time.sleep(1)

                        password_field.clear()
                        password_field.send_keys(password)
                        time.sleep(1)

                        # Tìm lại nút đăng nhập
                        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")

                        # Nhấn nút đăng nhập
                        print("Đang nhấn nút đăng nhập lần thứ hai...")
                        login_button.click()

                        # Đợi trang phản hồi
                        print("Đang đợi trang phản hồi lần thứ hai...")
                        time.sleep(10)
                    except Exception as e2:
                        print(f"Lỗi khi thử đăng nhập lần thứ hai: {e2}")
                        # Không làm gì thêm, tiếp tục kiểm tra kết quả đăng nhập

            # Kiểm tra đăng nhập thành công bằng nhiều cách
            print("Đang kiểm tra kết quả đăng nhập...")
            print(f"URL hiện tại: {driver.current_url}")
            print(f"Tiêu đề trang: {driver.title}")

            # Lưu screenshot để debug
            screenshot_path = f"login_result_{username}_{int(time.time())}.png"
            driver.save_screenshot(screenshot_path)
            print(f"Đã lưu ảnh màn hình tại: {screenshot_path}")

            # Kiểm tra các chỉ báo thành công
            success_indicators = [
                "dashboard" in driver.current_url,
                "account" in driver.current_url,
                "profile" in driver.current_url,
                "home" in driver.current_url,
                "slides" in driver.current_url,  # URL của trang khóa học
                "my" in driver.current_url,      # URL của trang cá nhân
                "logout" in driver.page_source.lower(),
                "sign out" in driver.page_source.lower(),
                "đăng xuất" in driver.page_source.lower(),
                username in driver.page_source,
                "login" not in driver.current_url.lower(),  # If we're no longer on the login page
                "web/login" not in driver.current_url.lower()  # Specific check for eco-tek.com.vn
            ]

            # Kiểm tra thêm các phần tử trên trang để xác định đăng nhập thành công
            try:
                # Kiểm tra các phần tử chỉ xuất hiện sau khi đăng nhập
                user_menu = driver.find_elements(By.XPATH, "//div[contains(@class, 'o_user_menu') or contains(@class, 'oe_topbar_name')]")
                if user_menu:
                    print("Đã tìm thấy menu người dùng, có thể đã đăng nhập thành công")
                    success_indicators.append(True)

                # Kiểm tra nút đăng xuất
                logout_buttons = driver.find_elements(By.XPATH, "//a[contains(@href, 'logout') or contains(text(), 'Logout') or contains(text(), 'Sign out') or contains(text(), 'Đăng xuất')]")
                if logout_buttons:
                    print("Đã tìm thấy nút đăng xuất, có thể đã đăng nhập thành công")
                    success_indicators.append(True)

                # Kiểm tra tên người dùng hiển thị
                user_display = driver.find_elements(By.XPATH, f"//*[contains(text(), '{username}')]")
                if user_display:
                    print(f"Đã tìm thấy tên người dùng {username} trên trang, có thể đã đăng nhập thành công")
                    success_indicators.append(True)
            except Exception as e:
                print(f"Lỗi khi kiểm tra các phần tử đăng nhập thành công: {e}")

            if any(success_indicators):
                print(f"Tài khoản {username} đăng nhập thành công!")

                # Lưu URL hiện tại để có thể quay lại sau này nếu cần
                original_url = driver.current_url
                print(f"Đăng nhập thành công, đang ở trang: {original_url}")

                # Open DevTools programmatically after successful login
                try:
                    print("Đang mở DevTools...")
                    # Use JavaScript to open DevTools with Network panel active
                    driver.execute_script("""
                    // First open DevTools
                    setTimeout(function() { 
                        // Use debugger statement to open DevTools
                        debugger; 

                        // Try to focus on Network panel after DevTools is opened
                        setTimeout(function() {
                            // This will work if DevTools is already open
                            if (window.chrome && window.chrome.devtools) {
                                try {
                                    // Try to switch to Network panel
                                    chrome.devtools.panels.setOpenPanel('network');
                                    console.log('Switched to Network panel');
                                } catch(e) {
                                    console.error('Error switching to Network panel:', e);
                                }
                            }
                        }, 1000);
                    }, 1000);
                    """)
                    print("DevTools đã được mở thành công")
                except Exception as devtools_error:
                    print(f"Lỗi khi mở DevTools: {devtools_error}")

                # Try to navigate to the course URL after successful login
                try:
                    course_url = "https://hoclythuyetlaixe.eco-tek.com.vn/slides/cau-tao-va-sua-chua-thong-thuong-xe-oto-283"
                    print(f"Đang chuyển hướng đến trang khóa học: {course_url}")
                    driver.get(course_url)
                    time.sleep(5)  # Wait for the page to load
                    print(f"Đã chuyển hướng đến trang: {driver.current_url}")

                    # Open DevTools again after navigation
                    try:
                        print("Đang mở DevTools sau khi chuyển hướng...")
                        # Use JavaScript to open DevTools with Network panel active
                        driver.execute_script("""
                        // First open DevTools
                        setTimeout(function() { 
                            // Use debugger statement to open DevTools
                            debugger; 

                            // Try to focus on Network panel after DevTools is opened
                            setTimeout(function() {
                                // This will work if DevTools is already open
                                if (window.chrome && window.chrome.devtools) {
                                    try {
                                        // Try to switch to Network panel
                                        chrome.devtools.panels.setOpenPanel('network');
                                        console.log('Switched to Network panel');
                                    } catch(e) {
                                        console.error('Error switching to Network panel:', e);
                                    }
                                }
                            }, 1000);
                        }, 1000);
                        """)
                        print("DevTools đã được mở thành công sau khi chuyển hướng")
                    except Exception as devtools_error:
                        print(f"Lỗi khi mở DevTools sau khi chuyển hướng: {devtools_error}")
                except Exception as e:
                    print(f"Lỗi khi chuyển hướng đến trang khóa học: {e}")

                return True
            else:
                print(f"Tài khoản {username} đăng nhập thất bại.")
                # Thử phương pháp cuối cùng: Điều hướng trực tiếp đến URL khóa học
                print("Đăng nhập thất bại, thử điều hướng trực tiếp đến URL khóa học...")
                try:
                    # Thử đăng nhập lại một lần nữa với JavaScript
                    print("Thử đăng nhập lại với JavaScript trước khi điều hướng trực tiếp...")
                    try:
                        # Tìm form đăng nhập
                        login_form = driver.find_element(By.TAG_NAME, "form")

                        # Tạo JavaScript để submit form
                        js_code = """
                        var form = document.querySelector('form');
                        var loginInput = form.querySelector('[name="login"]');
                        var passwordInput = form.querySelector('[name="password"]');

                        if (loginInput) {
                            loginInput.value = arguments[0];
                        }

                        if (passwordInput) {
                            passwordInput.value = arguments[1];
                        }

                        form.submit();
                        """

                        # Thực thi JavaScript
                        driver.execute_script(js_code, username, password)
                        print("Đã submit form đăng nhập bằng JavaScript")
                        time.sleep(10)  # Đợi trang phản hồi

                        # Kiểm tra lại xem có thành công không
                        if "login" not in driver.current_url.lower():
                            print("Đăng nhập bằng JavaScript thành công!")
                            return True
                    except Exception as js_error:
                        print(f"Lỗi khi thử đăng nhập bằng JavaScript: {js_error}")

                    # Thử điều hướng trực tiếp đến trang khóa học
                    course_url = "https://hoclythuyetlaixe.eco-tek.com.vn/slides/cau-tao-va-sua-chua-thong-thuong-xe-oto-283"
                    print(f"Đang chuyển hướng đến trang khóa học: {course_url}")
                    driver.get(course_url)
                    time.sleep(10)  # Đợi lâu hơn để đảm bảo trang đã tải xong

                    # Kiểm tra lại xem có thành công không
                    print(f"URL sau khi điều hướng trực tiếp: {driver.current_url}")
                    print(f"Tiêu đề trang sau khi điều hướng trực tiếp: {driver.title}")

                    # Lưu screenshot để debug
                    screenshot_path = f"direct_navigation_{username}_{int(time.time())}.png"
                    driver.save_screenshot(screenshot_path)
                    print(f"Đã lưu ảnh màn hình sau khi điều hướng trực tiếp tại: {screenshot_path}")

                    # Kiểm tra xem có bị chuyển hướng về trang login không
                    if "login" not in driver.current_url.lower():
                        print("Điều hướng trực tiếp thành công, không bị chuyển về trang login")

                        # Thử tìm các phần tử chỉ xuất hiện trong trang khóa học
                        try:
                            course_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'o_wslides_lesson_content') or contains(@class, 'o_wslides_lesson_main')]")
                            if course_elements:
                                print(f"Đã tìm thấy {len(course_elements)} phần tử khóa học, xác nhận đã vào được trang khóa học")
                                return True
                        except Exception as e:
                            print(f"Lỗi khi tìm phần tử khóa học: {e}")

                        # Nếu không tìm thấy phần tử khóa học cụ thể, vẫn trả về True vì URL không phải trang login
                        return True
                    else:
                        print("Điều hướng trực tiếp thất bại, bị chuyển về trang login")

                        # Thử một URL khóa học khác
                        try:
                            alternative_url = "https://hoclythuyetlaixe.eco-tek.com.vn/slides"
                            print(f"Thử URL khóa học thay thế: {alternative_url}")
                            driver.get(alternative_url)
                            time.sleep(10)

                            if "login" not in driver.current_url.lower():
                                print("Điều hướng đến URL thay thế thành công!")
                                return True
                            else:
                                print("Điều hướng đến URL thay thế thất bại")
                                return False
                        except Exception as alt_error:
                            print(f"Lỗi khi thử URL thay thế: {alt_error}")
                            return False
                except Exception as direct_nav_error:
                    print(f"Lỗi khi điều hướng trực tiếp: {direct_nav_error}")
                    return False

                return False

        except Exception as e:
            print(f"Lỗi khi đăng nhập với tài khoản {username}: {e}")
            # Chụp ảnh màn hình khi gặp lỗi để debug
            try:
                # Check if driver is defined and initialized
                if 'driver' in locals() and driver:
                    # Save screenshot directly in the project root directory
                    screenshot_path = f"error_screenshot_{username}_{int(time.time())}.png"
                    driver.save_screenshot(screenshot_path)
                    print(f"Đã lưu ảnh màn hình lỗi tại: {screenshot_path}")
                else:
                    print("Không thể lưu ảnh màn hình lỗi: Driver không được khởi tạo")
            except Exception as screenshot_error:
                print(f"Không thể lưu ảnh màn hình lỗi: {screenshot_error}")
                # Try with absolute path as fallback
                try:
                    if 'driver' in locals() and driver:
                        import os
                        # Get the current working directory (absolute path)
                        current_dir = os.getcwd()
                        screenshot_path = os.path.join(current_dir, f"error_screenshot_{username}_{int(time.time())}.png")
                        driver.save_screenshot(screenshot_path)
                        print(f"Đã lưu ảnh màn hình lỗi tại đường dẫn tuyệt đối: {screenshot_path}")
                except Exception as fallback_error:
                    print(f"Không thể lưu ảnh màn hình lỗi (cả phương án dự phòng): {fallback_error}")
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
