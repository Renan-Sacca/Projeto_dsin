import logging
import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class GoogleCalendarService:
    def __init__(self, access_token: str, refresh_token: str, token_expiry: datetime.datetime, client_id: str, client_secret: str):
        self.credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=["https://www.googleapis.com/auth/calendar.events"]
        )
        self.service = build("calendar", "v3", credentials=self.credentials)

    def create_event(self, title: str, description: str, start_time: datetime.datetime, end_time: datetime.datetime, add_alarm: bool = False):
        event = {
            "summary": title,
            "description": description,
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "America/Sao_Paulo",
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "America/Sao_Paulo",
            },
        }

        if add_alarm:
            event["reminders"] = {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 60}, # Alarme 1 hora antes
                    {"method": "popup", "minutes": 15}, # Alarme 15 minutos antes
                ],
            }

        try:
            created_event = self.service.events().insert(calendarId="primary", body=event).execute()
            logger.info(f"Evento criado no Google Calendar: {created_event.get('htmlLink')}")
            return created_event.get("id")
        except HttpError as error:
            logger.error(f"Erro ao criar evento no Google Calendar: {error}")
            return None

    def delete_event(self, event_id: str):
        try:
            self.service.events().delete(calendarId="primary", eventId=event_id).execute()
            logger.info(f"Evento deletado no Google Calendar: {event_id}")
            return True
        except HttpError as error:
            logger.error(f"Erro ao deletar evento no Google Calendar: {error}")
            return False
