# store/test/test_auth.py
from django.contrib.auth.models import User, Group
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import time

class AuthTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        # Usar Service para evitar problemas de permisos
        service = Service()
        cls.browser = webdriver.Chrome(service=service, options=options)
        cls.browser.implicitly_wait(10)
    
    @classmethod
    def tearDownClass(cls):
        try:
            if cls.browser:
                cls.browser.quit()
        except Exception as e:
            print(f"Error cerrando navegador: {e}")
        finally:
            super().tearDownClass()
    
    def setUp(self):
        """Crear usuario admin con permisos de staff"""
        # Crear grupos si no existen
        Group.objects.get_or_create(name='Administrador')
        Group.objects.get_or_create(name='Vendedor')
        
        # Crear usuario admin
        self.admin_user = User.objects.create_user(
            username="admin",
            password="admin123"
        )
        self.admin_user.is_staff = True
        self.admin_user.save()
        
        # Asignar al grupo Administrador
        admin_group = Group.objects.get(name='Administrador')
        self.admin_user.groups.add(admin_group)
        
        # Crear usuario vendedor
        self.vendedor_user = User.objects.create_user(
            username="vendedor",
            password="vendedor123"
        )
        vendedor_group = Group.objects.get(name='Vendedor')
        self.vendedor_user.groups.add(vendedor_group)
    
    def tearDown(self):
        """Limpiar después de cada test"""
        try:
            # Limpiar cookies
            self.browser.delete_all_cookies()
        except Exception as e:
            print(f"Error limpiando cookies: {e}")
    
    # =====================
    # LOGIN CORRECTO
    # =====================
    def test_login_success(self):
        """Verificar que el login funciona correctamente"""
        self.browser.get(f"{self.live_server_url}/login/")
        
        # Esperar a que cargue el formulario
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        
        # Llenar formulario
        self.browser.find_element(By.NAME, "username").send_keys("admin")
        self.browser.find_element(By.NAME, "password").send_keys("admin123")
        
        # Submit
        self.browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Esperar redirección
        WebDriverWait(self.browser, 10).until(
            lambda driver: "/login" not in driver.current_url
        )
        
        # Verificar que salió del login
        self.assertNotIn("/login", self.browser.current_url)
        print(f"✓ Login exitoso - Redirigido a: {self.browser.current_url}")
    
    # =====================
    # LOGIN INCORRECTO
    # =====================
    def test_login_fail(self):
        """Verificar que login con credenciales incorrectas falla"""
        self.browser.get(f"{self.live_server_url}/login/")
        
        # Esperar formulario
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        
        # Llenar con credenciales incorrectas
        self.browser.find_element(By.NAME, "username").send_keys("admin")
        self.browser.find_element(By.NAME, "password").send_keys("contraseña_incorrecta")
        
        # Submit
        self.browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Esperar un momento
        time.sleep(2)
        
        # Verificar que sigue en login
        self.assertIn("/login", self.browser.current_url)
        print(f"✓ Login fallido correctamente - Permanece en: {self.browser.current_url}")
    
    # =====================
    # PANEL ADMIN PROTEGIDO
    # =====================
    def test_admin_dashboard_requires_login(self):
        """Verificar que el panel admin requiere autenticación"""
        # Intentar acceder sin login
        self.browser.get(f"{self.live_server_url}/panel/dashboard/")
        
        # Esperar redirección a login
        WebDriverWait(self.browser, 10).until(
            EC.url_contains("/login")
        )
        
        # Verificar que redirigió a login
        self.assertIn("/login", self.browser.current_url)
        print(f"✓ Panel protegido - Redirigió a: {self.browser.current_url}")
    
    # =====================
    # PANEL DE VENTAS PROTEGIDO
    # =====================
    def test_sales_panel_requires_login(self):
        """Verificar que el panel de ventas requiere autenticación"""
        # Intentar acceder sin login
        self.browser.get(f"{self.live_server_url}/sale/multiple/")
        
        # Esperar redirección
        WebDriverWait(self.browser, 10).until(
            EC.url_contains("/login")
        )
        
        # Verificar redirección
        self.assertIn("/login", self.browser.current_url)
        print(f"✓ Panel de ventas protegido - Redirigió a: {self.browser.current_url}")
    
    # =====================
    # LOGOUT
    # =====================
    def test_logout(self):
        """Verificar que el logout funciona correctamente"""
        # Primero hacer login
        self.browser.get(f"{self.live_server_url}/login/")
        
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        
        self.browser.find_element(By.NAME, "username").send_keys("admin")
        self.browser.find_element(By.NAME, "password").send_keys("admin123")
        self.browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Esperar a que se complete el login
        WebDriverWait(self.browser, 10).until(
            lambda driver: "/login" not in driver.current_url
        )
        
        # Ahora hacer logout
        self.browser.get(f"{self.live_server_url}/logout/")
        
        # Esperar redirección a login
        WebDriverWait(self.browser, 10).until(
            EC.url_contains("/login")
        )
        
        # Verificar que redirigió a login
        self.assertIn("/login", self.browser.current_url)
        print(f"✓ Logout exitoso - Redirigió a: {self.browser.current_url}")
    
    # =====================
    # ACCESO ADMIN VS VENDEDOR
    # =====================
    def test_vendedor_cannot_access_admin_panel(self):
        """Verificar que vendedor NO puede acceder al panel admin"""
        # Login como vendedor
        self.browser.get(f"{self.live_server_url}/login/")
        
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        
        self.browser.find_element(By.NAME, "username").send_keys("vendedor")
        self.browser.find_element(By.NAME, "password").send_keys("vendedor123")
        self.browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Esperar login
        WebDriverWait(self.browser, 10).until(
            lambda driver: "/login" not in driver.current_url
        )
        
        # Intentar acceder al panel admin
        self.browser.get(f"{self.live_server_url}/panel/dashboard/")
        
        # Esperar un momento
        time.sleep(2)
        
        # Verificar que no puede acceder (redirige o muestra error)
        # El decorador @user_passes_test debería redirigir
        current_url = self.browser.current_url
        
        # Si tiene permisos, no debería poder ver el dashboard
        # Dependiendo de tu configuración, puede redirigir a login o a home
        self.assertNotEqual(current_url, f"{self.live_server_url}/panel/dashboard/")
        print(f"✓ Vendedor bloqueado del panel admin - URL actual: {current_url}")
    
    # =====================
    # ADMIN PUEDE ACCEDER A TODO
    # =====================
    def test_admin_can_access_admin_panel(self):
        """Verificar que admin SÍ puede acceder al panel admin"""
        # Login como admin
        self.browser.get(f"{self.live_server_url}/login/")
        
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        
        self.browser.find_element(By.NAME, "username").send_keys("admin")
        self.browser.find_element(By.NAME, "password").send_keys("admin123")
        self.browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Esperar login
        WebDriverWait(self.browser, 10).until(
            lambda driver: "/login" not in driver.current_url
        )
        
        # Acceder al panel admin
        self.browser.get(f"{self.live_server_url}/panel/dashboard/")
        
        # Esperar que cargue
        time.sleep(2)
        
        # Verificar que puede acceder
        self.assertIn("/panel/dashboard", self.browser.current_url)
        print(f"✓ Admin accede al panel correctamente - URL: {self.browser.current_url}")