import os
import tabula
import pandas as pd
from django.shortcuts import render
from django.views import View
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.core.files.base import ContentFile
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

    def read_pdf(self, input_file):
        try:
            pages = "all"
            dfs = tabula.read_pdf(input_file, pages=pages, multiple_tables=True, pandas_options={'dtype': str})
            if dfs:
                return dfs
            else:
                print("No tables found in the specified page range.")
                return None
        except Exception as e:
            print(f"An error occurred while parsing the PDF: {e}")
            return None


    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        uploaded_file = request.FILES.get("pdf_file")
        fs = FileSystemStorage()
        saved_file = None
        excel_path = None
        
        try:
            if uploaded_file:
                saved_file = fs.save(uploaded_file.name, uploaded_file)
                the_pdf_path = fs.path(saved_file)
                excel_path = os.path.join(os.path.dirname(the_pdf_path), f"{os.path.basename(the_pdf_path).split('.')[0]}.xlsx")
                dataframes = self.read_pdf(the_pdf_path)

                if dataframes:
                    all_data = pd.concat(dataframes, ignore_index=True)
                    all_data.to_excel(excel_path, index=False)

                    with open(excel_path, 'rb') as excel_file:
                        content = excel_file.read()
                        content_file = ContentFile(content)

                    response = HttpResponse(content_file.read(), content_type='application/vnd.ms-excel')
                    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(excel_file.name)}"'
                    return response
                else:
                    return HttpResponse("No data to save.")
            else:
                return HttpResponse("No file uploaded.")
        except Exception as e:
            return HttpResponse(f"An error occurred: {e}")
        finally:
            if saved_file:
                fs.delete(saved_file)
            if excel_path:
                fs.delete(excel_path)
