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

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View
import sqlite3
import json
import requests
from datetime import datetime

class DatabaseManagerView(LoginRequiredMixin, View):
    template_name = 'iconsignit_api.html'

    # Define a dictionary of column names and their desired data types
    desired_data_types = {
        "CreatedDate": "DATE",
        "ReleasedDate": "DATE",
        "ETADate": "DATE",
        "Cancelled": "DATE",
        "SPCode": "INTEGER",
        "RPCode": "INTEGER",
        "Volume": "REAL",
        "Weight": "REAL",
        "NetCharge": "REAL",
        "TaxCharge": "REAL",
        "TotalCharge": "REAL",
        "FreightCost": "REAL",
        "FreightFeesCost": "REAL",
        "NetCost": "REAL",
        "TaxCost": "REAL",
        "TotalCost": "REAL",
        "Margin": "REAL",
        "Collected": "DATE",
        "In Transit": "DATE",
        "Out for Delivery": "DATE",
        "Delivery": "DATE"
    }

    def create_table(self, conn, table_name, sample_data):
        """Create a table in the SQLite database based on the JSON keys with desired data types."""
        columns = []
        for key, value in sample_data.items():
            # Check if the column name is in the desired_data_types dictionary
            # If yes, use the desired data type; otherwise, use "TEXT"
            data_type = self.desired_data_types.get(key, "TEXT")
            columns.append(f'"{key}" {data_type}')
        
        columns_str = ', '.join(columns)
        create_table_query = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({columns_str});'
        conn.execute(create_table_query)
        conn.commit()

    # Function to convert date string to SQLite date format
    def convert_to_sqlite_date(self, date_str):
        try:
            # Parse the date string in DD/MM/YYYY format
            date_obj = datetime.strptime(date_str, "%d/%m/%Y")
            # Convert it to the SQLite date format (YYYY-MM-DD)
            sqlite_date = date_obj.strftime("%Y-%m-%d")
            return sqlite_date
        except ValueError:
            return None  # Return None for invalid date strings

    def record_exists(self, cursor, table_name, primary_key, record):
        """Check if a record exists in the table based on its primary key."""
        if primary_key is None or primary_key not in record:
            return False
        pk_value = record[primary_key]
        query = f'SELECT EXISTS(SELECT 1 FROM "{table_name}" WHERE "{primary_key}" = ? LIMIT 1)'
        cursor.execute(query, (pk_value,))
        return cursor.fetchone()[0] == 1

    def insert_data(self, cursor, table_name, data, primary_key):
        for record in data:
            # Convert date strings to SQLite date format
            for key, value in record.items():
                if key in self.desired_data_types and self.desired_data_types[key] == "DATE":
                    if value:
                        sqlite_date = self.convert_to_sqlite_date(value)
                        if sqlite_date:
                            record[key] = sqlite_date
                        else:
                            record[key] = None

            # Convert lists (or dicts) in the record to JSON strings
            processed_record = {k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in record.items()}

            # Replace empty strings with NULL
            for key, value in processed_record.items():
                if value == "":
                    processed_record[key] = None

            if not self.record_exists(cursor, table_name, primary_key, processed_record):
                columns = ', '.join([f'"{k}"' for k in processed_record.keys()])
                placeholders = ', '.join('?' * len(processed_record))
                query = f'INSERT INTO "{table_name}" ({columns}) VALUES ({placeholders})'
                values = tuple(processed_record.values())
                cursor.execute(query, values)

    def fetch_data(self, api_url):
        response = requests.get(api_url)
        if response.status_code == 200:
            json_data = response.json()
            return json_data['data']  # Adjust this according to your JSON structure
        else:
            # Handle errors appropriately
            return None

    def get(self, request):
        # SQLite database file path in your Linux directory
        db_file = "/home/ubuntu/tsa_project/iconsignit.db"

        # List of APIs
        api_list = [
            {"url": "https://tsa9.iconsignit.com.au/api/report/consign_detail_report?month_data=1", "table": "tsa_total", "primary_key": "ConnoteNumber"}
            ]

        connection = None
        response_data = []

        try:
            connection = sqlite3.connect(db_file)

            for api in api_list:
                data = self.fetch_data(api['url'])
                if data:
                    cursor = connection.cursor()
                    self.create_table(connection, api['table'], data[0])  # Assuming all data items have the same structure
                    self.insert_data(cursor, api['table'], data, api['primary_key'])
                    connection.commit()
                    response_data.append({'table': api['table'], 'status': 'success'})
                else:
                    response_data.append({'table': api['table'], 'status': 'failed', 'reason': 'No data received'})

            response_status = 200

        except sqlite3.Error as e:
            response_data = {'error': str(e)}
            response_status = 500

        finally:
            if connection:
                connection.close()

        return JsonResponse(response_data, status=response_status)

