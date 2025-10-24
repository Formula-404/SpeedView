import requests
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from apps.meeting.models import Meeting

OPENF1_API_BASE_URL = "https://api.openf1.org/v1"

class Command(BaseCommand):
    help = 'Mendownload dan menyimpan data Meeting dari OpenF1 API'

    def handle(self, *args, **options):
        self.stdout.write('Memulai proses fetch data meetings...')
        
        try:
            meetings_response = requests.get(f"{OPENF1_API_BASE_URL}/meetings")
            meetings_response.raise_for_status()
            meetings_data = meetings_response.json()
            meetings_created_count = 0
            meetings_updated_count = 0
            
            for m_data in meetings_data:
                defaults = {
                    'meeting_name': m_data.get('meeting_name'),
                    'circuit_short_name': m_data.get('circuit_short_name'),
                    'country_name': m_data.get('country_name'),
                    'year': m_data.get('year'),
                    'date_start': parse_datetime(m_data['date_start']) if m_data.get('date_start') else None,
                }
                
                obj, created = Meeting.objects.update_or_create(
                    meeting_key=m_data['meeting_key'],
                    defaults=defaults
                )
                
                if created:
                    meetings_created_count += 1
                else:
                    meetings_updated_count += 1
            
            self.stdout.write(self.style.SUCCESS(f'Meetings selesai: {meetings_created_count} dibuat, {meetings_updated_count} diperbarui.'))

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f'Gagal mengambil data dari OpenF1 API: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Terjadi error: {e}'))