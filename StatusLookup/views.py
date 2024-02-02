from django.shortcuts import render
from django.http import HttpResponse
from django.views import View
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from django.core.files.storage import FileSystemStorage
import pandas as pd
import os

class HomePageView(LoginRequiredMixin, View):
    login_url = 'login'  # Redirect to the login page if not logged in
    template_name = 'home.html'

    def get(self, request):
        context = {'username': request.user.username}
        return render(request, self.template_name, context)

class UserLoginView(LoginView):
    template_name = 'login.html'
    success_url = reverse_lazy('home')  # Redirect to home after successful login

class UserLogoutView(LoginRequiredMixin, LogoutView):
    next_page = reverse_lazy('login')

class StatusLookupView(LoginRequiredMixin, View):
    template_name = 'status_lookup.html'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver = None  # Initialize the WebDriver instance

    def get(self, request):
        return render(request, self.template_name)

    def get_geckodriver_path(self):
        # Update the Path when Uploading the code to a Server
        return "/home/sepehr_sky/Python/tsa_project/StatusLookup/geckodriver"

    def post(self, request):
        excel_file = request.FILES.get('excel_file')
        username = request.POST.get('username')  # Retrieve username from POST data
        password = request.POST.get('password')  # Retrieve password from POST data
        remember_me = request.POST.get('remember_me')  # Check if remember_me is in POST data

        if remember_me:
            # Store credentials securely (e.g., in session)
            request.session['remembered_username'] = request.POST.get('username')
            request.session['remembered_password'] = request.POST.get('password')
        else:
            # Clear any stored credentials if not remembered
            request.session.pop('remembered_username', None)
            request.session.pop('remembered_password', None)

        if username and password and excel_file:
            try:
                # Run the report
                result = self.run_report_threaded(username, password, excel_file)
                print("Result:", result)  # Add this line to print the result
                output_file_name = result

                messages.success(request, 'Process completed successfully.')  # Add a success message

                return result

            except WebDriverException as e:
                # Add an error message
                messages.error(request, f'Error: {e}')
        else:
            return HttpResponse("Invalid parameters")

    def run_report_threaded(self, username, password, excel_file):
        try:
            result_path = self.run_overdue_report(username, password, excel_file)
            print("Result path:", result_path)  # Add this line to print the result_path
            return result_path
        except Exception as e:
            return str(e)

    def run_overdue_report(self, username, password, excel_file):
        try:
            geckodriver_path = self.get_geckodriver_path()
            service = FirefoxService(executable_path=geckodriver_path)

            # Initialize the Firefox driver
            options = FirefoxOptions()
            options.headless = True
            driver = webdriver.Firefox(service=service, options=options)
            wait = WebDriverWait(driver, 10)

            # Open the login page
            driver.get('https://tsa9.iconsignit.com.au/login')

            # Log in to the website
            wait.until(EC.presence_of_element_located((By.NAME, 'email'))).send_keys(username)
            wait.until(EC.presence_of_element_located((By.NAME, 'password'))).send_keys(password)
            driver.find_element(By.XPATH, '//button[@type="submit"]').click()

            # Load the Excel file with pandas
            df = pd.read_excel(excel_file)

            # Initialize an empty list to store the statuses
            status_list = []

            for index, row in df.iterrows():
                consignment_number = row['ConnoteNumber']

                try:
                    # Navigate to the connotes page
                    driver.get('https://tsa9.iconsignit.com.au/admin/connotes')

                    # Find the input element for the consignment number search
                    consignment_input = wait.until(EC.presence_of_element_located((By.ID, 'cu_search_0')))

                    # Clear the input field and enter the consignment number
                    consignment_input.clear()
                    consignment_input.send_keys(consignment_number)

                    # Press Enter to perform the search
                    consignment_input.send_keys(Keys.ENTER)

                    # Wait for the "view" button to be clickable
                    view_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[text()="view"]')))

                    # Click on the "view" button
                    view_button.click()

                    # Locate the input element
                    tracking_status_input = driver.find_element(By.XPATH, '//input[@id="last_tracking_status"]')

                    # Get the value attribute, which contains the text
                    tracking_status = tracking_status_input.get_attribute('value')

                    # Add the text of the status element to the status list
                    status_list.append(tracking_status)

                except (NoSuchElementException, TimeoutException):
                    # If there's an error or timeout finding the element, print an empty string
                    status_list.append("Deleted")
                except Exception as e:
                    # If there's a different kind of error, append an empty string to the status list and print the error
                    status_list.append("error")
                    print(f"Encountered an error with {consignment_number}: {e}")
                    continue  # Move on to the next consignment number

            # Add the status list as a new column to the dataframe
            df['Status'] = status_list

            # Extract the original file name without extension
            file_name_without_extension, _ = os.path.splitext(excel_file.name)

            # Create a response with the processed data
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="{file_name_without_extension}_StatusLookup.xlsx"'

            with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Sheet1', index=False)

            return response

        except WebDriverException as e:
            print(e)
        finally:
            driver.quit()

    def update_status(self, message):
        messages.info(self.request, message)
