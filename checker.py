# checker.py
import requests
from icalendar import Calendar
from datetime import datetime
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ========================= CONFIG =========================
ROOMS = {
    "Room 1": {
        "Airbnb": "https://www.airbnb.com/calendar/ical/694116191964099772.ics?t=7c5625fe49f74a60a59632bf6431ffea&locale=en-GB",
        "Booking.com": "https://ical.booking.com/v1/export?t=0f450afe-6ade-4dd9-b5eb-1041ce2cbdb4",
        "Expedia": "https://www.expediapartnercentral.com/calendars/export/f162377092544b3aa0642ca4bab041e2.ics"
    },
    "Room 2": {
        "Airbnb": "https://www.airbnb.com/calendar/ical/760381506346386631.ics?t=c85b0fe48f28426ea39007d423723a66&locale=en-GB",
        "Booking.com": "https://ical.booking.com/v1/export?t=a3730f5c-5a25-48ab-8309-5ad2ecb05334",
        "Expedia": "https://www.expediapartnercentral.com/calendars/export/3b1cf8c8dd494455b3abe313151d7bfb.ics"
    },
    "Room 3": {
        "Airbnb": "https://www.airbnb.com/calendar/ical/1245886426463556063.ics?t=6d8bb1d960de4f899d9aca8388041c9a&locale=en-GB",
        "Booking.com": "https://ical.booking.com/v1/export?t=2df24b10-2e8a-42ca-a277-21364b36f098",
        "Expedia": "https://www.expediapartnercentral.com/calendars/export/858d9f323b0b44f186f49e11b95ed722.ics"
    },
    "Room 4": {
        "Airbnb": "https://www.airbnb.com/calendar/ical/1246485565817681763.ics?t=b22259dd82e941ce969315b12e25e2c6&locale=en-GB",
        "Booking.com": "https://ical.booking.com/v1/export?t=41a55623-f268-4635-bf75-2fbfd9db0b1f",
        "Expedia": "https://www.expediapartnercentral.com/calendars/export/819e2d704d7e4c3f862b3f7caef701d2.ics"
    },
    "Room 5": {
        "Airbnb": "https://www.airbnb.com/calendar/ical/1246505901003017630.ics?t=b7c95a3853fb4de3b23814df5e0bc8d9&locale=en-GB",
        "Booking.com": "https://ical.booking.com/v1/export?t=db628adc-8d5b-4f7c-8f1b-f67283158122",
        "Expedia": "https://www.expediapartnercentral.com/calendars/export/4cf1b126abeb4152846bced84a7df521.ics"
    },
    "Room 6": {
        "Airbnb": "https://www.airbnb.com/calendar/ical/1246515707851544151.ics?t=16c77f7b49564be3a2707479a8166ca0&locale=en-GB",
        "Booking.com": "https://ical.booking.com/v1/export?t=e0739e76-f1c6-4fe9-9274-f1645da8acd9",
        "Expedia": "https://www.expediapartnercentral.com/calendars/export/5de95d892f2646b5af92dabeaf3c91b3.ics"
    }
}

HISTORY_FILE = "bookings_history.json"

EMAIL_CONFIG = {
    "sender": "corchorooms@gmail.com",
    "password": os.getenv("GMAIL_APP_PASSWORD"),
    "recipient": "corchorooms@gmail.com",
}
# ========================================================

# ... [Rest of the code remains exactly the same as previous version] ...

def send_alert(overlaps):
    if not overlaps:
        return

    msg = MIMEMultipart()
    msg['From'] = EMAIL_CONFIG["sender"]
    msg['To'] = EMAIL_CONFIG["recipient"]
    msg['Subject'] = f"🚨 DOUBLE BOOKING ALERT - {len(overlaps)} issue(s) found"

    body = "Double bookings detected!\n\n"
    for a, b in overlaps:
        body += f"Room: {a['room']}\n"
        body += f"• {a['platform']}: {a['summary']} ({a['start'].strftime('%Y-%m-%d')})\n"
        body += f"• {b['platform']}: {b['summary']} ({b['start'].strftime('%Y-%m-%d')})\n\n"

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_CONFIG["sender"], EMAIL_CONFIG["password"])
        server.send_message(msg)
        server.quit()
        print("✅ Alert email sent successfully!")
    except Exception as e:
        print(f"❌ Email failed: {e}")

# ===================== MAIN =====================
def main():
    print(f"🔍 Double Booking + History Tracker started at {datetime.now()}")
    
    history = load_history()
    all_events = []
    new_bookings = 0

    for room_name, platforms in ROOMS.items():
        print(f"\nChecking {room_name}...")
        room_events = []
        
        for platform, url in platforms.items():
            cal = fetch_ical(url)
            events = get_events(cal, room_name, platform)
            room_events.extend(events)
            all_events.extend(events)

            for event in events:
                uid = event['uid']
                if uid and uid not in history:
                    history[uid] = {
                        "uid": uid,
                        "room": event['room'],
                        "platform": event['platform'],
                        "summary": event['summary'],
                        "start": event['start'].isoformat(),
                        "end": event['end'].isoformat(),
                        "status": event['status'],
                        "first_seen": datetime.now().isoformat()
                    }
                    new_bookings += 1
                    print(f"   ✅ New booking saved: {room_name} - {event['summary']}")

        overlaps = find_overlaps(room_events)
        if overlaps:
            print(f"   ⚠️  {len(overlaps)} overlap(s) found in {room_name}")

    global_overlaps = find_overlaps(all_events)
    
    if global_overlaps:
        print(f"🚨 Total double bookings found: {len(global_overlaps)}")
        send_alert(global_overlaps)
    else:
        print("✅ No double bookings found.")

    save_history(history)
    print(f"📊 Total bookings in history: {len(history)} | New today: {new_bookings}")

if __name__ == "__main__":
    main()
