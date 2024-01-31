import tabula
import pandas as pd
from django.shortcuts import render
from django.views import View
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.core.files.uploadedfile import InMemoryUploadedFile


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

class PdfToExcelView(LoginRequiredMixin, View):
    template_name = 'pdf_to_excel.html'

    def read_pdf(self, input_file, start_page, multiple_page):
        try:
            pages = start_page if not multiple_page else str(start_page) + "-"
            dfs = tabula.read_pdf(input_file, pages=pages, multiple_tables=True, pandas_options={'dtype': str})
            return dfs
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        try:
            # Get the uploaded file from request.FILES
            uploaded_file = request.FILES.get("pdf_file")
            
            # Check if a file was uploaded
            if uploaded_file:
                # Save the uploaded file temporarily
                fs = FileSystemStorage()
                saved_file = fs.save(uploaded_file.name, uploaded_file)

                # Construct the file path
                the_pdf = fs.path(saved_file)
                
                # Extract other form data
                start_page = int(request.POST.get("start_page"))
                multiple_page = request.POST.get("multiple_page") == "true"

                # Read PDF and process data
                dataframes = self.read_pdf(the_pdf, start_page, multiple_page)

                if dataframes:
                    all_data = pd.concat(dataframes, ignore_index=True)
                    excel_file = saved_file + ".xlsx"
                    excel_path = fs.path(excel_file)
                    
                    # Save data to Excel
                    all_data.to_excel(excel_path, index=False)
                    
                    # Prepare response with Excel file
                    with open(excel_path, 'rb') as excel_file:
                        response = HttpResponse(excel_file.read(), content_type='application/vnd.ms-excel')
                        response['Content-Disposition'] = 'attachment; filename=' + excel_file.name
                    return response
                else:
                    return HttpResponse("No data to save.")
            else:
                return HttpResponse("No file uploaded.")
        except Exception as e:
            return HttpResponse(f"An error occurred: {e}")
