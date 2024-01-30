import os
import pandas as pd
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.shortcuts import render

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

class ConnoteCompareView(LoginRequiredMixin, View):
    login_url = 'login'
    template_name = 'fileprocessor.html'  # Create an HTML template for file upload

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        try:
            file1 = request.FILES['file1']
            file2 = request.FILES['file2']

            if file1.name.endswith('.xlsx') and file2.name.endswith('.xlsx'):
                # Save the uploaded files to a temporary location
                fs = FileSystemStorage()
                filename1 = fs.save(file1.name, file1)
                filename2 = fs.save(file2.name, file2)
                try:
                    # Read the Excel files
                    df1 = pd.read_excel(filename1)
                    df2 = pd.read_excel(filename2)

                    # Compare the 'connote' column and create a new dataframe
                    df2['Status'] = df2.apply(
                        lambda row: 'NEW' if row['ConnoteNumber'] not in df1['ConnoteNumber'].values else 'Already Exists',
                        axis=1
                    )

                    # Extract the name of the first uploaded file without extension
                    first_file_name = os.path.splitext(file1.name)[0]

                    # Create a response with the processed data
                    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    response['Content-Disposition'] = f'attachment; filename="{first_file_name}_ConnoteCompare.xlsx"'

                    # Save the new dataframe to the response object
                    with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
                        df2.to_excel(writer, sheet_name='Sheet1', index=False)
                finally:
                    # Delete the temporary files
                    fs.delete(filename1)
                    fs.delete(filename2)

                return response
            else:
                return HttpResponse("Both files must be in .xlsx format.")
        except Exception as e:
            return HttpResponse(f"An error occurred: {str(e)}")
