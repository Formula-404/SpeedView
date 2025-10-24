import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from apps.circuit.models import Circuit
import re
from urllib.parse import urljoin

class Command(BaseCommand):
    help = 'Mengambil data sirkuit F1 dari Wikipedia dan menyimpannya ke database.'

    WIKI_URL = "https://en.wikipedia.org/wiki/List_of_Formula_One_circuits"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    def find_main_circuit_table(self, soup):
        """
        Mencari tabel utama yang berisi data sirkuit berdasarkan header kolomnya.
        """
        all_tables = soup.find_all('table', {'class': 'wikitable sortable'})
        self.stdout.write(f'Menemukan {len(all_tables)} tabel dengan kelas wikitable sortable.')

        expected_headers_partial = ['circuit', 'map', 'type', 'location', 'country', 'last length used', 'turns']

        for i, table in enumerate(all_tables):
            self.stdout.write(f'Menganalisis tabel ke-{i+1}...')
            header_row = table.find('tr')
            if not header_row:
                self.stdout.write(f' -> Melewatkan tabel ke-{i+1}, tidak ada baris header.')
                continue

            headers = [th.text.strip().lower() for th in header_row.find_all('th')]
            self.stdout.write(f' -> Header ditemukan: {headers}')

            if all(expected_header in headers for expected_header in expected_headers_partial):
                self.stdout.write(self.style.SUCCESS(f' -> Tabel ke-{i+1} cocok! Menggunakan tabel ini.'))
                return table

        self.stdout.write(self.style.ERROR('Tidak dapat menemukan tabel sirkuit utama dengan header yang diharapkan.'))
        return None


    def handle(self, *args, **options):
        self.stdout.write(f'Memulai scraping dari: {self.WIKI_URL}')

        try:
            response = requests.get(self.WIKI_URL, headers=self.HEADERS)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f'Gagal mengambil halaman Wikipedia: {e}'))
            return

        soup = BeautifulSoup(response.content, 'html.parser')
        target_table = self.find_main_circuit_table(soup)

        if not target_table:
            return

        circuits_added = 0
        circuits_updated = 0
        rows = target_table.find('tbody').find_all('tr')

        header_cells = rows[0].find_all('th')
        headers = [th.text.strip().lower() for th in header_cells]
        try:
            name_idx = headers.index('circuit')
            map_idx = headers.index('map')
            type_idx = headers.index('type')
            direction_idx = headers.index('direction')
            location_idx = headers.index('location')
            country_idx = headers.index('country')
            length_idx = headers.index('last length used')
            turns_idx = headers.index('turns')
            gp_name_idx = headers.index('grands prix')
            seasons_idx = headers.index('season(s)')
            gp_held_idx = headers.index('grands prix held')
        except ValueError as e:
            self.stdout.write(self.style.ERROR(f"Gagal menemukan header kolom yang diharapkan di tabel terpilih: {e}. Header: {headers}"))
            return

        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])

            if len(cells) != len(headers):
                 self.stdout.write(self.style.WARNING(f'Melewatkan baris karena jumlah sel ({len(cells)}) tidak sesuai header ({len(headers)})'))
                 continue

            try:
                name_tag = cells[name_idx].find('a')
                name = name_tag.text.strip() if name_tag else cells[name_idx].text.strip()
                if not name:
                    continue

                image_url = None
                image_tag = cells[map_idx].find('img')
                if image_tag and image_tag.has_attr('src'):
                    img_src = image_tag['src']
                    image_url = 'https:' + img_src if img_src.startswith('//') else urljoin(self.WIKI_URL, img_src)

                circuit_type_text = cells[type_idx].text.strip().upper()
                circuit_type_map = {'STREET CIRCUIT': 'STREET', 'ROAD CIRCUIT': 'ROAD', 'RACE CIRCUIT': 'RACE'}
                circuit_type = circuit_type_map.get(circuit_type_text, 'RACE')

                direction_text = cells[direction_idx].text.strip().upper()
                direction_map = {'CLOCKWISE': 'CW', 'ANTI-CLOCKWISE': 'ACW', 'COUNTER-CLOCKWISE': 'ACW'}
                direction = direction_map.get(direction_text, 'CW')

                location_tag = cells[location_idx].find('a')
                location = location_tag.text.strip() if location_tag else cells[location_idx].text.strip()

                country_cell = cells[country_idx]
                country_tag = country_cell.find('a')
                if country_tag and country_tag.text.strip():
                    country = country_tag.text.strip()
                else:
                    for span in country_cell.find_all('span'):
                        span.decompose()
                    country = country_cell.text.strip()
                self.stdout.write(f'  -> Nama: {name}, Negara diekstrak: "{country}"')
                length_text = cells[length_idx].text.strip().split('\n')[0].replace(' km', '').split(' ')[0]
                try: length_km = float(length_text)
                except ValueError: length_km = 0.0

                turns_text = cells[turns_idx].text.strip()
                turns_match = re.match(r'(\d+)', turns_text)
                turns = int(turns_match.group(1)) if turns_match else 0

                grands_prix = cells[gp_name_idx].text.strip()
                seasons = cells[seasons_idx].text.strip().replace('\n', ', ')

                gp_held_text = cells[gp_held_idx].text.strip()
                gp_held_match = re.match(r'(\d+)', gp_held_text)
                try: grands_prix_held = int(gp_held_match.group(1)) if gp_held_match else 0
                except ValueError: grands_prix_held = 0

                circuit, created = Circuit.objects.update_or_create(
                    name=name,
                    defaults={
                        'country': country,
                        'location': location,
                        'circuit_type': circuit_type,
                        'direction': direction,
                        'length_km': length_km,
                        'turns': turns,
                        'grands_prix': grands_prix,
                        'seasons': seasons,
                        'grands_prix_held': grands_prix_held,
                        'map_image_url': image_url,
                        'is_admin_created': False
                    }
                )

                if created:
                    circuits_added += 1
                else:
                    circuits_updated += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error saat memproses baris untuk "{name}": {e}'))

        self.stdout.write(self.style.SUCCESS(f'Scraping selesai: {circuits_added} sirkuit ditambahkan, {circuits_updated} sirkuit diperbarui.'))