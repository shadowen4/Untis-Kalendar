import os
import datetime
import requests

HOST = "https://dbgqui.webuntis.com"
SCHOOL = os.environ["UNTIS_SCHOOL"]
USER = os.environ["UNTIS_USER"]
PASSWORD = os.environ["UNTIS_PASSWORD"]
WOCHEN = 4

s = requests.Session()

# 1. Anmelden
r = s.post(
    f"{HOST}/WebUntis/j_spring_security_check",
    data={
        "school": SCHOOL,
        "j_username": USER,
        "j_password": PASSWORD,
        "token": "",
    },
    headers={"Accept": "application/json"},
)
print("Login:", r.status_code, r.text[:200])
r.raise_for_status()

# 2. Token holen
r = s.get(f"{HOST}/WebUntis/api/token/new")
print("Token:", r.status_code)
r.raise_for_status()
s.headers["Authorization"] = "Bearer " + r.text.strip()

# 3. Eigene Kennung holen
r = s.get(f"{HOST}/WebUntis/api/rest/view/v1/app/data")
print("App-Daten:", r.status_code)
r.raise_for_status()
person_id = r.json()["user"]["person"]["id"]

# 4. Stundenplan holen
heute = datetime.date.today()
start = heute - datetime.timedelta(days=heute.weekday())
ende = start + datetime.timedelta(weeks=WOCHEN)

r = s.get(
    f"{HOST}/WebUntis/api/rest/view/v1/timetable/entries",
    params={
        "start": start.isoformat(),
        "end": ende.isoformat(),
        "format": 1,
        "resourceType": "STUDENT",
        "resources": person_id,
        "timetableType": "MY_TIMETABLE",
    },
)
print("Stundenplan:", r.status_code)
r.raise_for_status()
daten = r.json()


def ics_zeit(text):
    return text.replace("-", "").replace(":", "") + "00"


stamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S")

zeilen = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//untis-bridge//DE",
    "X-WR-CALNAME:Schule",
]

anzahl = 0
for tag in daten.get("days", []):
    for e in tag.get("gridEntries", []):
        faecher, raeume = [], []
        for key, werte in e.items():
            if key.startswith("position") and isinstance(werte, list):
                for w in werte:
                    cur = w.get("current") or {}
                    name = cur.get("shortName") or cur.get("longName") or ""
                    if cur.get("type") == "SUBJECT" and name:
                        faecher.append(name)
                    elif cur.get("type") == "ROOM" and name:
                        raeume.append(name)

        titel = ", ".join(faecher) or "Unterricht"
        status = e.get("status", "REGULAR")
        if status == "CANCELLED":
            titel = "ENTFÄLLT: " + titel
        elif status != "REGULAR":
            titel = "ÄNDERUNG: " + titel

        beginn = ics_zeit(e["duration"]["start"])
        schluss = ics_zeit(e["duration"]["end"])
        zeilen += [
            "BEGIN:VEVENT",
            f"UID:{e.get('ids', [''])[0]}-{beginn}@untis-bridge",
            f"DTSTAMP:{stamp}Z",
            f"DTSTART:{beginn}",
            f"DTEND:{schluss}",
            f"SUMMARY:{titel}",
            f"LOCATION:{', '.join(raeume)}",
            "END:VEVENT",
        ]
        anzahl += 1

zeilen.append("END:VCALENDAR")

with open("stundenplan.ics", "w", encoding="utf-8") as f:
    f.write("\r\n".join(zeilen))

print(f"Fertig: {anzahl} Stunden geschrieben.")
