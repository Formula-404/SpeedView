import requests
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from apps.meeting.models import Meeting
from apps.session.models import Session

OPENF1_API_BASE_URL = "https://api.openf1.org/v1"

class Command(BaseCommand):
    help = 'Mendownload dan menyimpan data Meeting dan Session dari OpenF1 API'

    def handle(self, *args, **options):
        self.stdout.write('Memulai proses fetch data...')
        
        # 1. Fetch dan simpan Meetings
        self.stdout.write('Mengambil data meetings...')
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
                
                # Buat atau update meeting
                obj, created = Meeting.objects.update_or_create(
                    meeting_key=m_data['meeting_key'],
                    defaults=defaults
                )
                
                if created:
                    meetings_created_count += 1
                else:
                    meetings_updated_count += 1
            
            self.stdout.write(self.style.SUCCESS(f'Meetings selesai: {meetings_created_count} dibuat, {meetings_updated_count} diperbarui.'))

            # 2. Fetch dan simpan Sessions
            self.stdout.write('Mengambil data sessions untuk setiap meeting...')
            sessions_created_count = 0
            sessions_updated_count = 0

            all_meeting_keys = Meeting.objects.values_list('meeting_key', flat=True)            
            for meeting_key in all_meeting_keys:
                self.stdout.write(f'  - Mengambil session untuk meeting_key: {meeting_key}...', ending=' ')
                try:
                    sessions_response = requests.get(f"{OPENF1_API_BASE_URL}/sessions?meeting_key={meeting_key}")
                    sessions_response.raise_for_status()
                    sessions_data = sessions_response.json()
                    
                    if not sessions_data:
                        self.stdout.write('Tidak ada data.')
                        continue

                    for s_data in sessions_data:
                        session_defaults = {
                            'meeting_key': s_data.get('meeting_key'),
                            'name': s_data.get('session_name'),
                            'start_time': parse_datetime(s_data['date_start']) if s_data.get('date_start') else None,
                        }
                        
                        s_obj, s_created = Session.objects.update_or_create(
                            session_key=s_data['session_key'],
                            defaults=session_defaults
                        )
                        
                        if s_created:
                            sessions_created_count += 1
                        else:
                            sessions_updated_count += 1
                            
                    self.stdout.write(f'Selesai ({len(sessions_data)} sesi).')
                
                except requests.exceptions.RequestException as e:
                    self.stdout.write(self.style.ERROR(f'Gagal mengambil session untuk {meeting_key}: {e}'))

            self.stdout.write(self.style.SUCCESS(f'Sessions selesai: {sessions_created_count} dibuat, {sessions_updated_count} diperbarui.'))
            self.stdout.write(self.style.SUCCESS('Semua data berhasil di-fetch dan disimpan.'))

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f'Gagal total mengambil data dari OpenF1 API: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Terjadi error: {e}'))