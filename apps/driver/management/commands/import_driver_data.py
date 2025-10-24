import json
import time
import ssl
from json import JSONDecodeError
from typing import Dict, List, Optional, Tuple, Union
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandError

from apps.driver.models import Driver, DriverEntry
from apps.meeting.models import Meeting
from apps.team.models import Team

try:
    import certifi 
    _CAFILE = certifi.where()
except Exception:
    _CAFILE = None

BASE_URL = "https://api.openf1.org/v1/drivers"


class Command(BaseCommand):
    help = "Import/update Driver rows from OpenF1 /v1/drivers."

    def add_arguments(self, parser):
        parser.add_argument("--driver-number", type=int, action="append", dest="driver_numbers")
        parser.add_argument("--country", action="append", dest="country_codes")
        parser.add_argument("--sleep", type=float, default=0.0)
        parser.add_argument("--create-only", action="store_true")
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--timeout", type=float, default=10.0)
        parser.add_argument("--debug", action="store_true")
        parser.add_argument(
            "--insecure", action="store_true",
            help="DEV ONLY: skip TLS certificate verification."
        )
        parser.add_argument(
            "--entry",
            action="store_true",
            help="Also upsert DriverEntry rows for each driver/session.",
        )

    def handle(self, *args, **options):
        driver_numbers: List[int] = options.get("driver_numbers") or []
        country_codes: List[str] = options.get("country_codes") or []
        sleep_time: float = options["sleep"]
        create_only: bool = options["create_only"]
        dry_run: bool = options["dry_run"]
        create_entries: bool = options["entry"]
        self._timeout: float = options["timeout"]
        self._debug: bool = options["debug"]

        insecure = bool(options.get("insecure"))
        if insecure:
            self.stdout.write(self.style.WARNING("[warn] Using INSECURE SSL context (no certificate verification)."))
            self._ssl_ctx = ssl._create_unverified_context()
        else:
            self._ssl_ctx = ssl.create_default_context(cafile=_CAFILE) if _CAFILE else ssl.create_default_context()

        params: Dict[str, Union[int, str, List[Union[int, str]]]] = {}
        if driver_numbers:
            params["driver_number"] = driver_numbers
        if country_codes:
            params["country_code"] = [c.upper() for c in country_codes]

        try:
            batch = self._fetch_batch(params)
        except (HTTPError, URLError) as exc:
            raise CommandError(f"Failed to fetch drivers: {exc}") from exc

        if not batch:
            self.stdout.write(self.style.WARNING("No driver rows returned."))
            return

        if self._debug:
            self.stdout.write(self.style.NOTICE(f"[debug] received {len(batch)} rows"))

        if dry_run:
            self.stdout.write(f"Dry-run: would process {len(batch)} rows.")
            return

        created, updated, entries_created, entries_updated = self._store_batch(
            batch=batch,
            create_only=create_only,
            create_entries=create_entries,
        )

        message = f"Done. processed={len(batch)}, created={created}, updated={updated}"
        if create_entries:
            message += f", entry_created={entries_created}, entry_updated={entries_updated}"
        self.stdout.write(self.style.SUCCESS(message))

        if sleep_time:
            time.sleep(sleep_time)

    # ---------------- helpers ----------------

    def _build_url(self, base: str, params: Dict[str, Union[int, str, List[Union[int, str]]]]) -> str:
        qs = urlencode(params, doseq=True)  # ?p=1&p=2
        return f"{base}?{qs}" if qs else base

    def _fetch_batch(self, params: Dict[str, Union[int, str, List[Union[int, str]]]]) -> List[dict]:
        url = self._build_url(BASE_URL, params)
        if self._debug:
            self.stdout.write(self.style.NOTICE(f"[debug] GET {url}"))
        req = Request(url, headers={"User-Agent": "openf1-driver-import/1.0 (+https://openf1.org/)"})
        # ---- NEW: pass SSL context
        with urlopen(req, timeout=self._timeout, context=self._ssl_ctx) as response:
            payload = response.read()

        try:
            data = json.loads(payload)
        except JSONDecodeError as exc:
            raise CommandError(f"Invalid JSON for URL {url}: {exc}") from exc

        if not isinstance(data, list):
            return []
        return data

    def _store_batch(
        self,
        batch: List[dict],
        create_only: bool,
        create_entries: bool,
    ) -> Tuple[int, int, int, int]:
        created = updated = 0
        entries_created = entries_updated = 0
        for row in batch:
            dn = self._to_int(row.get("driver_number"))
            if dn is None:
                continue
            defaults = {
                "first_name": (row.get("first_name") or "")[:64],
                "last_name": (row.get("last_name") or "")[:64],
                "full_name": (row.get("full_name") or "").strip()[:128],
                "broadcast_name": (row.get("broadcast_name") or "").strip()[:128],
                "name_acronym": (row.get("name_acronym") or "").strip().upper()[:3],
                "country_code": (row.get("country_code") or "").strip().upper()[:3],
                "headshot_url": (row.get("headshot_url") or "").strip(),
            }
            if create_only:
                if not Driver.objects.filter(pk=dn).exists():
                    Driver.objects.create(driver_number=dn, **defaults)
                    created += 1
                continue
            driver, was_created = Driver.objects.update_or_create(
                driver_number=dn,
                defaults=defaults,
            )
            if was_created:
                created += 1
            else:
                updated += 1

            if create_entries:
                entry_created, entry_updated = self._upsert_entry(driver=driver, row=row)
                entries_created += entry_created
                entries_updated += entry_updated
        return created, updated, entries_created, entries_updated

    def _to_int(self, value) -> Optional[int]:
        try:
            return int(value)
        except Exception:
            return None

    def _upsert_entry(self, driver: Driver, row: dict) -> Tuple[int, int]:
        meeting_key = self._to_int(row.get("meeting_key"))
        session_key = self._to_int(row.get("session_key"))
        if meeting_key is None or session_key is None:
            return 0, 0

        meeting, _ = Meeting.objects.get_or_create(meeting_key=meeting_key)

        team_name = (row.get("team_name") or "").strip()
        team_colour_value = (row.get("team_colour") or "").strip().upper()[:6]
        team: Optional[Team] = None
        if team_name:
            team_colour = team_colour_value or "000000"
            team_defaults = {"team_colour": team_colour}
            team, created = Team.objects.get_or_create(
                team_name=team_name,
                defaults=team_defaults,
            )
            if not created and team_colour and team.team_colour != team_colour:
                team.team_colour = team_colour
                team.save(update_fields=["team_colour"])

        entry_defaults = {
            "meeting": meeting,
            "team": team,
            "team_colour": team_colour_value,
        }
        entry, created = DriverEntry.objects.get_or_create(
            driver=driver,
            session_key=session_key,
            defaults=entry_defaults,
        )
        if created:
            return 1, 0

        dirty_fields: List[str] = []
        if entry.meeting_id != meeting.pk:
            entry.meeting = meeting
            dirty_fields.append("meeting")
        team_id = team.pk if team else None
        if entry.team_id != team_id:
            entry.team = team
            dirty_fields.append("team")
        if team_colour_value and entry.team_colour != team_colour_value:
            entry.team_colour = team_colour_value
            dirty_fields.append("team_colour")
        if dirty_fields:
            entry.save(update_fields=dirty_fields)
            return 0, 1
        return 0, 0
