import os
import datetime
import webuntis

SERVER = "dbgqui.webuntis.com"
SCHOOL = os.environ["UNTIS_SCHOOL"]
USERNAME = os.environ["UNTIS_USER"]
PASSWORD = os.environ["UNTIS_PASSWORD"]
WOCHEN = 4

s = webuntis.Session(
    server=SERVER,
    username=USERNAME,
    password=PASSWORD,
    school=SCHOOL,
    useragent="untis-bridge",
).login()

auth = s._request(
    "authenticate",
    {"user": USERNAME, "password": PASSWORD, "client": "untis-bridge"},
)
person_id = auth["personId"]
person_type = auth["personType"]

heute = datetime.date.today()
start = heute - datetime.timedelta(days=heute.weekday())
ende = start + datetime.timedelta(weeks=WOCHEN)

rows = s._request(
    "getTimetable",
    {
        "options": {
            "element": {"id": person_id, "type": person_type},
            "startDate": int(start.strftime("%Y%m%d")),
            "endDate": int(ende.strftime("%Y%m%d")),
        }
    },
)

faecher = {x.id: x.name for x in s.subjects()}
raeume = {x.id: x.name for x in s.rooms()}


def namen(liste, tabelle):
    return ", ".join(
        tabelle.get(x["id"], x.get("name", "")) for x in liste or []
    )


stamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S")

zeilen = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//untis-bridge//DE",
    "X-WR-CALNAME:Schule",
]

for r in rows:
    titel = namen(r.get("su"), faecher) or "Unterricht"
    if r.get("code") == "cancelled":
        titel = "ENTFÄLLT: " + titel
    elif r.get("code") == "irregular":
        titel = "VERTRETUNG: " + titel
    tag = str(r["date"])
    beginn = f"{tag}T{r['startTime']:04d}00"
    schluss = f"{tag}T{r['endTime']:04d}00"
    zeilen += [
        "BEGIN:VEVENT",
        f"UID:{r['id']}-{beginn}@untis-bridge",
        f"DTSTAMP:{stamp}Z",
        f"DTSTART:{beginn}",
        f"DTEND:{schluss}",
        f"SUMMARY:{titel}",
        f"LOCATION:{namen(r.get('ro'), raeume)}",
        "END:VEVENT",
    ]

zeilen.append("END:VCALENDAR")

with open("stundenplan.ics", "w", encoding="utf-8") as f:
    f.write("\r\n".join(zeilen))

s.logout()
print(f"Fertig: {len(rows)} Stunden geschrieben.")
