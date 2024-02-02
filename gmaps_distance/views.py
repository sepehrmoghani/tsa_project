from io import BytesIO
import pandas as pd
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.shortcuts import render

import googlemaps

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

class GmapsdistanceView(LoginRequiredMixin, View):
    template_name = 'gmaps_distance.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        file = request.FILES['file']
        if file.name.endswith('.xlsx'):
            fs = FileSystemStorage()
            excel_file = fs.save(file.name, file)

            try:
                # Read the list of addresses from the uploaded Excel file
                addresses_df = pd.read_excel(excel_file)

                # Calculate distances
                distances_df = pd.DataFrame(self.calculate_distances(addresses_df))

                # Save the distances DataFrame to an Excel file in-memory
                in_memory_excel = BytesIO()
                distances_df.to_excel(in_memory_excel, index=False)

                # Create an HTTP response with the Excel content
                response = HttpResponse(in_memory_excel.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = f'attachment; filename="postcode_distances.xlsx"'

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

    def calculate_distances(self, df):
        # Add the 'Tonne' column by dividing 'Weight' by 1000
        df['Tonne'] = df['Weight'] / 1000
        
        # Initialize an empty list for distances
        distances = []

        # Initialize the Google Maps Geocoding API client with your API key
        gmaps = googlemaps.Client(key='AIzaSyBakGS0A92qhgqMM1pglVpcUB2qawp1M04')
        
        for index, row in df.iterrows():
            # Construct the full address for sender and receiver
            origin_address = f"{row['SLocality']} {row['SState']} {row['SPCode']}"
            destination_address = f"{row['RLocality']} {row['RState']} {row['RPCode']}"

            # Make the API call with the full addresses
            distance_result = gmaps.distance_matrix(origins=origin_address, destinations=destination_address, mode='driving')

            # Check if the result is valid and contains the 'distance' data
            element = distance_result['rows'][0]['elements'][0]
            if element['status'] == 'OK':
                distance_text = element['distance']['text']
                # Append only the distance value to the distances list
                distances.append(distance_text)
            else:
                # Handle the case where no distance could be found
                print(f"Distance not found for {origin_address} to {destination_address}, status was {element['status']}")
                distances.append('Not found')

        # Add the 'EST KM\'s' column to the DataFrame
        df['EST KM\'s'] = distances
        
        # Select only the specified columns
        final_columns = [
            'ReleasedDate', 'ConnoteNumber', 'SLocality', 'SState', 'SPCode',
            'RLocality', 'RState', 'RPCode', 'Items', 'Weight', 'Tonne',
            'Volume', 'EST KM\'s'
        ]
        df_final = df[final_columns]
        
        return df_final