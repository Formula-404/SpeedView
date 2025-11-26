import requests
import re
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from apps.circuit.models import Circuit
from urllib.parse import urljoin

class Command(BaseCommand):
    help = 'Mengambil data sirkuit F1 dari Wikipedia dan menyimpannya ke database.'

    WIKI_URL = "https://en.wikipedia.org/wiki/List_of_Formula_One_circuits"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    def clean_text(self, text):
        """Membersihkan teks dari referensi wiki, spasi berlebih, dan koma ganda."""
        if not text:
            return ""
        text = re.sub(r'\[.*?\]', '', text)
        text = text.replace('\xa0', ' ')
        text = text.replace('\n', ',')        
        items = [item.strip() for item in text.split(',') if item.strip()]        
        return ', '.join(items)

    def extract_number(self, text, is_float=False):
        """Mengambil angka pertama dari string menggunakan Regex."""
        if not text:
            return 0.0 if is_float else 0
        
        text = re.sub(r'\[.*?\]', '', text)        
        pattern = r"(\d+\.\d+)" if is_float else r"(\d+)"
        match = re.search(pattern, text)
        
        if match:
            try:
                return float(match.group(1)) if is_float else int(match.group(1))
            except ValueError:
                pass
        return 0.0 if is_float else 0

    def find_main_circuit_table(self, soup):
        all_tables = soup.find_all('table', {'class': 'wikitable sortable'})
        self.stdout.write(f'Menemukan {len(all_tables)} tabel potensial.')

        for i, table in enumerate(all_tables):
            headers = [th.text.strip().lower() for th in table.find_all('th')]
            if 'circuit' in headers and 'map' in headers:
                self.stdout.write(self.style.SUCCESS(f' -> Tabel ke-{i+1} cocok.'))
                return table
        return None

    def handle(self, *args, **options):
        self.stdout.write(f'Memulai scraping dari: {self.WIKI_URL}')

        try:
            response = requests.get(self.WIKI_URL, headers=self.HEADERS)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f'Gagal koneksi: {e}'))
            return

        soup = BeautifulSoup(response.content, 'html.parser')
        target_table = self.find_main_circuit_table(soup)

        if not target_table:
            self.stdout.write(self.style.ERROR('Tabel tidak ditemukan.'))
            return

        circuits_added = 0
        circuits_updated = 0
        
        header_row = target_table.find('tr')
        headers = [th.text.strip().lower() for th in header_row.find_all('th')]
        
        idxs = {}
        for i, h in enumerate(headers):
            if 'circuit' in h: idxs['name'] = i
            elif 'map' in h: idxs['map'] = i
            elif 'type' in h: idxs['type'] = i
            elif 'direction' in h: idxs['dir'] = i
            elif 'location' in h: idxs['loc'] = i
            elif 'country' in h: idxs['country'] = i
            elif 'length' in h: idxs['len'] = i
            elif 'turns' in h: idxs['turns'] = i
            elif 'held' in h: idxs['held'] = i 
            elif 'grands prix' in h: idxs['gp'] = i
            elif 'season' in h: idxs['season'] = i

        rows = target_table.find_all('tr')[1:]

        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 5: continue 

            try:
                # 1. NAME
                name_cell = cells[idxs.get('name', 0)]
                name = self.clean_text(name_cell.text)
                if not name: continue
                
                # 2. MAP IMAGE
                image_url = None
                if 'map' in idxs:
                    map_cell = cells[idxs['map']]
                    img_tag = map_cell.find('img')
                    if img_tag and img_tag.has_attr('src'):
                        src = img_tag['src']
                        image_url = 'https:' + src if src.startswith('//') else src

                # 3. TYPE
                circuit_type = 'RACE'
                if 'type' in idxs:
                    type_text = self.clean_text(cells[idxs['type']].text).upper()
                    if 'STREET' in type_text: circuit_type = 'STREET'
                    elif 'ROAD' in type_text: circuit_type = 'ROAD'

                # 4. DIRECTION
                direction = 'CW'
                if 'dir' in idxs:
                    dir_text = self.clean_text(cells[idxs['dir']].text).upper()
                    if 'ANTI' in dir_text or 'COUNTER' in dir_text: direction = 'ACW'

                # 5. LOCATION & COUNTRY
                location = self.clean_text(cells[idxs.get('loc', 4)].text)
                country = self.clean_text(cells[idxs.get('country', 5)].text)

                # 6. LENGTH
                length_km = 0.0
                if 'len' in idxs:
                    len_text = cells[idxs['len']].text
                    length_km = self.extract_number(len_text, is_float=True)

                # 7. TURNS
                turns = 0
                if 'turns' in idxs:
                    turns_text = cells[idxs['turns']].text
                    turns = self.extract_number(turns_text, is_float=False)

                # 8. GP HELD
                grands_prix_held = 0
                if 'held' in idxs:
                    held_text = cells[idxs['held']].text
                    grands_prix_held = self.extract_number(held_text, is_float=False)

                # 9. GP NAMES
                grands_prix = ""
                if 'gp' in idxs:
                    grands_prix = self.clean_text(cells[idxs['gp']].text)

                # 10. SEASONS
                seasons = ""
                if 'season' in idxs:
                    seasons = self.clean_text(cells[idxs['season']].text)

                obj, created = Circuit.objects.update_or_create(
                    name=name,
                    defaults={
                        'map_image_url': image_url,
                        'circuit_type': circuit_type,
                        'direction': direction,
                        'location': location,
                        'country': country,
                        'length_km': length_km,
                        'turns': turns,
                        'grands_prix': grands_prix,
                        'seasons': seasons,
                        'grands_prix_held': grands_prix_held,
                        'is_admin_created': False
                    }
                )

                if created: circuits_added += 1
                else: circuits_updated += 1
                
                self.stdout.write(f"Processed: {name}")

            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Skip row error: {e}"))

        self.stdout.write(self.style.SUCCESS(f'Selesai: {circuits_added} baru, {circuits_updated} update.'))