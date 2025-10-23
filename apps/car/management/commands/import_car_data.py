import json
import time
from json import JSONDecodeError
from typing import Dict, Iterable, List, Optional, Tuple, Union
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_datetime

from apps.car.models import Car
from apps.meeting.models import Meeting
from apps.session.models import Session


BASE_URL = "https://api.openf1.org/v1/car_data"
SESS_URL = "https://api.openf1.org/v1/sessions"


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--meeting-key",
            type=int,
            action="append",
            dest="meeting_keys",
        )
        parser.add_argument(
            "--driver-number",
            type=int,
            action="append",
            dest="driver_numbers",
        )
        parser.add_argument(
            "--session-key",
            type=int,
            action="append",
            dest="session_keys",
        )
        parser.add_argument(
            "--sleep",
            type=float,
            default=0.0,
            help="Optional sleep (in seconds) between API calls to avoid rate limiting.",
        )
        parser.add_argument(
            "--min-speed",
            type=float,
            dest="min_speed",
        )
        parser.add_argument(
            "--create-only",
            action="store_true",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
        )
        parser.add_argument(
            "--timeout",
            type=float,
            default=10.0,
        )
        parser.add_argument(
            "--debug",
            action="store_true",
        )

    def handle(self, *args, **options):
        meeting_keys = self._resolve_meeting_keys(options["meeting_keys"])
        if not meeting_keys:
            raise CommandError("No meeting keys found. Add meetings first or pass --meeting-key.")

        session_keys = options.get("session_keys") or []
        driver_numbers = options.get("driver_numbers") or []
        sleep_time = options["sleep"]
        dry_run = options["dry_run"]
        create_only = options["create_only"]
        min_speed = options.get("min_speed")
        self._http_timeout: float = options["timeout"]
        self._debug: bool = options["debug"]

        total_created = 0
        total_updated = 0
        total_rows = 0
        self._meeting_cache: Dict[int, Meeting] = {}
        self._session_cache: Dict[int, Session] = {}

        for meeting_key in meeting_keys:
            rows, created, updated = self._process_meeting(
                meeting_key=meeting_key,
                session_keys=session_keys,
                driver_numbers=driver_numbers,
                dry_run=dry_run,
                create_only=create_only,
                sleep_time=sleep_time,
                min_speed=min_speed,
            )
            if rows == 0:
                self.stdout.write(self.style.WARNING(
                    f"[-] meeting {meeting_key}: no telemetry returned (or request failed)."
                ))
            else:
                msg = f"[+] meeting {meeting_key}: processed {rows} rows"
                if not dry_run:
                    msg += f" (created={created}, updated={updated})"
                self.stdout.write(self.style.SUCCESS(msg))

            total_rows += rows
            total_created += created
            total_updated += updated

        summary = f"Finished. Total rows: {total_rows}"
        if dry_run:
            summary += " (dry run – no database changes)."
        else:
            summary += f", created: {total_created}, updated: {total_updated}."
        self.stdout.write(summary)

    def _resolve_meeting_keys(self, cli_values: Optional[List[int]]) -> List[int]:
        if cli_values:
            return cli_values
        return list(
            Meeting.objects.order_by("meeting_key").values_list("meeting_key", flat=True)
        )

    def _session_keys_for_meeting(self, meeting_key: int) -> List[int]:
        """Fetch session keys for a meeting and ensure Session rows exist locally."""
        url = f"{SESS_URL}?meeting_key={meeting_key}"
        req = Request(url, headers={"User-Agent": "openf1-import/1.0"})
        with urlopen(req, timeout=self._http_timeout) as r:
            payload = r.read()
        try:
            data = json.loads(payload)
        except JSONDecodeError as exc:
            raise CommandError(f"Invalid JSON from sessions API for meeting {meeting_key}: {exc}") from exc
        if not isinstance(data, list):
            return []

        keys: List[int] = []
        for row in data:
            try:
                session_key = int(row["session_key"])
            except Exception:
                continue

            meeting_obj, session_obj = self._ensure_related_objects(meeting_key, session_key)
            name = row.get("session_name") or row.get("name") or ""
            start_time = row.get("session_start") or row.get("date_start") or row.get("date")
            update_fields: List[str] = []
            if session_obj and name and session_obj.name != name:
                session_obj.name = name
                update_fields.append("name")
            if session_obj and start_time:
                parsed = parse_datetime(start_time)
                if parsed and session_obj.start_time != parsed:
                    session_obj.start_time = parsed
                    update_fields.append("start_time")
            if session_obj and update_fields:
                session_obj.save(update_fields=update_fields)

            keys.append(session_key)
        return keys

    def _process_meeting(
        self,
        meeting_key: int,
        session_keys: Iterable[int],
        driver_numbers: Iterable[int],
        dry_run: bool,
        create_only: bool,
        sleep_time: float,
        min_speed: Optional[float],
    ) -> Tuple[int, int, int]:
        rows = created = updated = 0
        self._ensure_related_objects(meeting_key, None)

        if session_keys:
            session_list = list(session_keys)
        else:
            try:
                session_list = self._session_keys_for_meeting(meeting_key)
                if not session_list:
                    self.stdout.write(self.style.WARNING(
                        f"[-] meeting {meeting_key}: no sessions found."
                    ))
                    session_list = [None] 
            except Exception as e:
                self.stdout.write(self.style.WARNING(
                    f"[!] meeting {meeting_key}: failed to fetch sessions ({e}); fallback to meeting-only queries."
                ))
                session_list = [None]

        dn_list = list(driver_numbers) if driver_numbers else [None]

        for session_key in session_list:
            for driver_number in dn_list:
                params: Dict[str, Union[int, float, str]] = {
                    "meeting_key": meeting_key,
                }
                if session_key is not None:
                    params["session_key"] = session_key
                if driver_number is not None:
                    params["driver_number"] = driver_number
                if min_speed is not None:
                    params["speed>"] = min_speed  

                if self._debug:
                    self.stdout.write(f"[debug] GET {self._build_url(BASE_URL, params)}")

                try:
                    batch = self._fetch_batch(params)
                except HTTPError as exc:
                    body = ""
                    try:
                        body = exc.read().decode(errors="replace")
                    except Exception:
                        pass
                    if exc.code == 422:
                        snippet = (body or "").strip().replace("\n", " ")
                        self.stdout.write(self.style.WARNING(
                            f"[-] meeting {meeting_key} session {session_key}: 422 – {snippet[:240]}"
                        ))
                        continue
                    raise CommandError(f"API request failed {exc.code}: {body}") from exc
                except URLError as exc:
                    raise CommandError(f"Network error: {exc}") from exc

                if not batch:
                    continue

                try:
                    batch_created, batch_updated = self._store_batch(
                        batch=batch,
                        dry_run=dry_run,
                        create_only=create_only,
                    )
                except Exception as exc:
                    raise CommandError(
                        f"DB error while storing batch for meeting {meeting_key}, session {session_key}: {exc}"
                    ) from exc

                rows += len(batch)
                created += batch_created
                updated += batch_updated

                if sleep_time:
                    time.sleep(sleep_time)

        return rows, created, updated

    def _ensure_related_objects(
        self, meeting_key: int, session_key: Optional[int]
    ) -> Tuple[Meeting, Optional[Session]]:
        meeting = self._meeting_cache.get(meeting_key)
        if meeting is None:
            meeting, _ = Meeting.objects.get_or_create(meeting_key=meeting_key)
            self._meeting_cache[meeting_key] = meeting

        session = None
        if session_key is not None:
            session = self._session_cache.get(session_key)
            if session is None:
                session, _ = Session.objects.get_or_create(
                    session_key=session_key,
                    defaults={'meeting': meeting},
                )
                if meeting and session.meeting_id is None:
                    session.meeting = meeting
                    session.save(update_fields=['meeting'])
                self._session_cache[session_key] = session

        return meeting, session

    def _build_url(self, base: str, params: Dict[str, Union[int, float, str]]) -> str:
        return f"{base}?{urlencode(params)}"

    def _fetch_batch(self, params: Dict[str, Union[int, float, str]]) -> List[dict]:
        url = self._build_url(BASE_URL, params)
        req = Request(
            url,
            headers={"User-Agent": "openf1-import/1.0 (+https://openf1.org/)"},
        )
        with urlopen(req, timeout=self._http_timeout) as response:
            payload = response.read()  
        try:
            data = json.loads(payload)
        except JSONDecodeError as exc:
            raise CommandError(f"Invalid JSON for URL {url}: {exc}") from exc
        if not isinstance(data, list):
            return []
        if self._debug:
            self.stdout.write(f"[debug] ← {len(data)} rows")
        return data

    def _store_batch(
        self,
        batch: List[dict],
        dry_run: bool,
        create_only: bool,
    ) -> Tuple[int, int]:
        created = updated = 0

        for entry in batch:
            if dry_run:
                continue

            meeting_obj, session_obj = self._ensure_related_objects(
                entry["meeting_key"], entry["session_key"]
            )

            defaults = {
                "meeting_key": meeting_obj,
                "session_key": session_obj,
                "brake": entry.get("brake", 0),
                "drs": entry.get("drs", 0),
                "n_gear": entry.get("n_gear", 0),
                "rpm": entry.get("rpm", 0),
                "speed": entry.get("speed", 0),
                "throttle": entry.get("throttle", 0),
            }

            if create_only:
                Car.objects.create(
                    driver_number=entry["driver_number"],
                    session_key=session_obj,
                    meeting_key=meeting_obj,
                    date=parse_datetime(entry["date"]),
                    brake=defaults["brake"],
                    drs=defaults["drs"],
                    n_gear=defaults["n_gear"],
                    rpm=defaults["rpm"],
                    speed=defaults["speed"],
                    throttle=defaults["throttle"],
                    is_manual=False,
                )
                created += 1
                continue

            obj, was_created = Car.objects.update_or_create(
                driver_number=entry["driver_number"],
                session_key=session_obj,
                date=parse_datetime(entry["date"]),
                defaults=defaults,
            )
            if was_created:
                created += 1
            else:
                updated += 1

        return created, updated
