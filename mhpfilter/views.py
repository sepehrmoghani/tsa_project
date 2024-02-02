import os
import tempfile
from django.shortcuts import render
from django.views import View
from django.urls import reverse_lazy
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.http import FileResponse

# Import custom functions or classes
from mhpfilter.mhp_module import read_pdf, brittany_filter

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

class MHFFilterView(LoginRequiredMixin, View):
    template_name = 'index.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        pdf_file = request.FILES.get("pdf_file")

        # Save the uploaded PDF file to a temporary location using FileSystemStorage
        fs = FileSystemStorage()
        temp_pdf_path = fs.save(pdf_file.name, pdf_file)

        try:
            dfs = read_pdf(temp_pdf_path)
            filtered_rows = brittany_filter(dfs)

            # Create a temporary directory to store the Excel file
            with tempfile.TemporaryDirectory() as temp_dir:
                output_file_path = os.path.join(temp_dir, f"{temp_pdf_path.split('.')[0]}_filtered_MHP.xlsx")

                # Save the filtered rows to the Excel file
                filtered_rows.to_excel(output_file_path, index=False)

                # Read the Excel file into a ContentFile
                with open(output_file_path, 'rb') as excel_file:
                    content = excel_file.read()
                    content_file = ContentFile(content)

                # Send the Excel file as a response for download using FileResponse
                response = FileResponse(content_file, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = f'attachment; filename="{os.path.basename(output_file_path)}"'

                return response

        except Exception as e:
            error_message = f"An error occurred: {e}"
            print(error_message)
            return render(request, self.template_name, {'error_message': error_message})

        finally:
            # Delete the temporary PDF file and the local copy of the Excel file
            fs.delete(temp_pdf_path)




