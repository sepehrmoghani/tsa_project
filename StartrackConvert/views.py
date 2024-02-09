import os
import pandas as pd
from io import BytesIO
from django.views import View
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import render
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin

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
    login_url = 'login'
    template_name = 'startrackconvert.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        file = request.FILES['file1']
        if file.name.endswith('.xlsx'):
            fs = FileSystemStorage()
            excel_file = fs.save(file.name, file)

            try:
                # Read the list of addresses from the uploaded Excel file
                addresses_df = pd.read_excel(excel_file, sheet_name='Invoice Charges')

                sorted_df = pd.DataFrame(self.process_dataframe(addresses_df))

                # Save the distances DataFrame to an Excel file in-memory
                in_memory_excel = BytesIO()
                sorted_df.to_excel(in_memory_excel, index=False)

                # Create an HTTP response with the Excel content
                response = HttpResponse(in_memory_excel.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = f'attachment; filename="{os.path.splitext(file.name)[0]}_converted.xlsx"'

                # Display success message
                messages.success(request, 'Distance calculation completed successfully.')

                return response

            except Exception as e:
                error_message = f"An error occurred: {e}"
                # Display error message
                messages.error(request, error_message)
                return render(request, self.template_name, {'error_message': error_message})
            finally:
                fs.delete(excel_file)
                
        else:
            error_message = "Please upload an Excel file."
            # Display error message
            messages.error(request, error_message)
            return render(request, self.template_name, {'error_message': error_message})


    def process_dataframe(self, source_df):
        
        new_columns = ["Date","Reference","Sender Reference","Sender Name","Sender Town","Sender Postcode","Receiver Name",
                "Receiver Town","Receiver Postcode","Route Code","Items","Pallets","Kg","m3","Cubic Kg","Fue Levy","GST",
                "Nett (Ex GST & FL)","Total Price","Description","Service"]

        new_df = pd.DataFrame(columns=new_columns)

        # Populate the new DataFrame with values from the source DataFrame
        for index, row in source_df.iterrows():
            new_row = {
                "Date": [row["Despatch date"]],
                'Reference': row['Connote/Job Number'],
                'Sender Reference': row['Reference 1'],
                'Sender Name': row['Senders Name'],
                'Sender Town': row['Senders Location'],
                'Receiver Name': row['Receiver Name 1'],
                'Receiver Town': row['Receiver Location'],
                'Receiver Postcode': row['Receiver Postcode'],
                'Items': row['Items Connote'],
                'Kg': row['Charge Weight'],
                'm3': row['Cube'],
                'Fue Levy': [row['Fuel Surcharge'] + row['Security Surcharge']],
                'GST': row['GST'],
                'Nett (Ex GST & FL)': row['Cost'],
                'Total Price': row['Total Charge'],
                'Service': row['Service Type']
            }
            new_row_df = pd.DataFrame(new_row)
            new_row_df = new_row_df.dropna(axis='columns', how='all')  # Ensure no all-NA columns are included
            new_df = pd.concat([new_df, new_row_df], ignore_index=True)


        return new_df
