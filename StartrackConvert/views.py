from django.shortcuts import render
from django.views import View
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
import os
import pandas as pd

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

class StartrackInvoiceConvertView(View):
    template_name = 'startrackconvert.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        if 'excel_file' in request.FILES:
            excel_file = request.FILES['excel_file']

            # Save the uploaded Excel file to a temporary location using FileSystemStorage
            fs = FileSystemStorage()
            temp_excel_path = fs.save(excel_file.name, excel_file)

            try:
                # Read the list of addresses from the uploaded Excel file
                source_df = pd.read_excel(temp_excel_path)

                # Initialize the new DataFrame with columns
                new_columns = ["Date", "Reference", "Sender Reference", "Sender Name", "Sender Town", "Receiver Name",
                               "Receiver Town", "Receiver Postcode", "Route Code", "Items", "Kg", "m3", "Fue Levy",
                               "GST", "Nett (Ex GST & FL)", "Total Price", "Service"]

                new_df = pd.DataFrame(columns=new_columns)

                # Populate the new DataFrame with values from the source DataFrame
                for index, row in source_df.iterrows():
                    new_row = {
                        "Date": [row["Despatch date"]],
                        'Reference': [row['Connote/Job Number']],
                        'Sender Reference': [row['Reference 1']],
                        'Sender Name': [row['Senders Name']],
                        'Sender Town': [row['Senders Location']],
                        'Receiver Name': [row['Receiver Name 1']],
                        'Receiver Town': [row['Receiver Location']],
                        'Receiver Postcode': [row['Receiver Postcode']],
                        'Items': [row['Items Connote']],
                        'Kg': [row['Charge Weight']],
                        'm3': [row['Cube']],
                        'Fue Levy': [row['Fuel Surcharge'] + row['Security Surcharge']],
                        'GST': [row['GST']],
                        'Nett (Ex GST & FL)': [row['Cost']],
                        'Total Price': [row['Total Charge']],
                        'Service': [row['Service Type']]
                    }

                    new_row_df = pd.DataFrame(new_row)
                    new_row_df = new_row_df.dropna(axis='columns', how='all')  # Ensure no all-NA columns are included
                    new_df = pd.concat([new_df, new_row_df], ignore_index=True)

                # Extract the directory path from the full Excel file path
                directory = os.path.dirname(temp_excel_path)
                # Extract the base name without extension for the new CSV file name
                base_name = os.path.basename(temp_excel_path).replace('.xlsx', '')
                new_excel_file_path = os.path.join(directory, f"{base_name}_converted.xlsx")  # Join directory with new file name

                new_df.to_excel(new_excel_file_path, index=False)

                # Create a response with the CSV file
                with open(new_excel_file_path, 'rb') as excel_file:
                    response = HttpResponse(excel_file.read(), content_type='text/csv')
                    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(new_excel_file_path)}"'

                # Delete the temporary Excel and CSV files from FileSystemStorage
                fs.delete(temp_excel_path)
                os.remove(new_excel_file_path)

                return response

            except Exception as e:
                error_message = f"An error occurred: {e}"
                return render(request, self.template_name, {'error_message': error_message})

        else:
            error_message = "Please upload an Excel file."
            return render(request, self.template_name, {'error_message': error_message})
