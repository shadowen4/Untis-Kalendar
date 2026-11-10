import os
import datetime
import webuntis

SERVER = "dbgqui.webuntis.com"
SCHOOL = os.environ["UNTIS_SCHOOL"]
USERNAME = os.environ["UNTIS_USER"]
PASSWORD = os.environ["UNTIS_PASSWORD"]
WOCHEN = 4


def zeit(dt):
    return dt.strftime("%Y%m%dT%H%M%S")


s = webuntis.Session(
    server=SERVER,
    username=USERNAME,
    password=PASSWORD,
    school=SCHOOL,
    useragent="untis-bridge",
).login()

heute = datetime.date.today()
start = heute - datetime.timedelta(days=heute.weekday())
ende = start + datetime.timedelta(weeks=WOCHEN)

schueler = s.students().filter(surname="Güther", fore_name="Benedikt")[0]
plan = s.timetable(student=schueler, start=start, end=ende)

zeilen = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//untis-bridge//DE",
    "X-WR-CALNAME:Schule",
]

for st in plan:
    fach = ", ".join(f.name for f in st.subjects) or "Unterricht"
    raum = ", ".join(r.name for r in st.rooms)
    if st.code == "cancelled":
        fach = "ENTFÄLLT: " + fach
    elif st.code == "irregular":
        fach = "VERTRETUNG: " + fach
    zeilen += [
        "BEGIN:VEVENT",
        f"UID:{st.id}-{zeit(st.start)}@untis-bridge",
        f"DTSTAMP:{zeit(datetime.datetime.utcnow())}Z",
        f"DTSTART:{zeit(st.start)}",
        f"DTEND:{zeit(st.end)}",
        f"SUMMARY:{fach}",
        f"LOCATION:{raum}",
        "END:VEVENT",
    ]

zeilen.append("END:VCALENDAR")

with open("stundenplan.ics", "w", encoding="utf-8") as f:
    f.write("\r\n".join(zeilen))

s.logout()
print(f"Fertig: {len(plan)} Stunden geschrieben.")
