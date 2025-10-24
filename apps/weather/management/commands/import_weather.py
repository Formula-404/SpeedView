import requests
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from apps.meeting.models import Meeting
from apps.weather.models import Weather
from django.db import IntegrityError

OPENF1_API_BASE_URL = "https://api.openf1.org/v1"

class Command(BaseCommand):
    help = 'Mendownload dan menyimpan data Weather dari OpenF1 API untuk semua meeting'

    def handle(self, *args, **options):
        self.stdout.write('Memulai proses fetch data weather...')        
        all_meetings = Meeting.objects.all()
        if not all_meetings.exists():
            self.stdout.write(self.style.ERROR('Database Meeting kosong. Harap jalankan "python manage.py fetch_meetings" terlebih dahulu.'))
            return

        self.stdout.write(f'Akan mengambil data cuaca untuk {all_meetings.count()} meetings...')
        weather_created_count = 0
        weather_updated_count = 0
        for meeting in all_meetings:
            self.stdout.write(f'  - Mengambil cuaca untuk: {meeting.meeting_name} ({meeting.year})...', ending=' ')
            try:
                weather_response = requests.get(f"{OPENF1_API_BASE_URL}/weather?meeting_key={meeting.meeting_key}")
                weather_response.raise_for_status()
                weather_data = weather_response.json()
                
                if not weather_data:
                    self.stdout.write('Tidak ada data.')
                    continue

                for w_data in weather_data:
                    entry_date = parse_datetime(w_data['date']) if w_data.get('date') else None
                    if not entry_date:
                        continue

                    defaults = {
                        'air_temperature': w_data.get('air_temperature'),
                        'track_temperature': w_data.get('track_temperature'),
                        'pressure': w_data.get('pressure'),
                        'wind_speed': w_data.get('wind_speed'),
                        'wind_direction': w_data.get('wind_direction'),
                        'humidity': w_data.get('humidity'),
                        'rainfall': w_data.get('rainfall', False) or False, # Pastikan boolean
                    }
                    
                    try:
                        obj, created = Weather.objects.update_or_create(
                            meeting=meeting,
                            date=entry_date,
                            defaults=defaults
                        )
                        if created:
                            weather_created_count += 1
                        else:
                            weather_updated_count += 1
                    except IntegrityError:
                        self.stdout.write(self.style.WARNING(f'Skipped duplicate entry for {meeting.meeting_key} at {entry_date}'))
                
                self.stdout.write(f'Selesai ({len(weather_data)} entri).')

            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f'Gagal: {e}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error saat memproses data: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Weather selesai: {weather_created_count} dibuat, {weather_updated_count} diperbarui.'))