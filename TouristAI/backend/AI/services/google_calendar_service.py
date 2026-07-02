import os
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar']

# File paths in backend/AI directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, "client_secret.json")

class GoogleCalendarService:
    def __init__(self, user_id: str = "guest_user") -> None:
        self.user_id = user_id
        # User-specific token storage
        self.token_path = os.path.join(BASE_DIR, f"token_{user_id}.json")

    def is_configured(self) -> bool:
        """
        Returns True if Google Calendar credentials are configured.
        """
        if os.path.exists(CLIENT_SECRETS_FILE):
            return True
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        return bool(client_id and client_secret)

    def _get_client_config(self) -> Dict[str, Any]:
        """
        Loads Google client credentials from client_secret.json or environment variables.
        """
        if os.path.exists(CLIENT_SECRETS_FILE):
            try:
                with open(CLIENT_SECRETS_FILE, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to read client_secret.json: {e}")

        # Fallback to environment variables
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/oauth2callback")
        
        if not client_id or not client_secret:
            raise ValueError(
                "Google Calendar API credentials missing. Provide client_secret.json "
                "or set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET env vars."
            )

        return {
            "web": {
                "client_id": client_id,
                "project_id": os.getenv("GOOGLE_PROJECT_ID", "tourist-ai-project"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": client_secret,
                "redirect_uris": [redirect_uri]
            }
        }

    def get_credentials(self) -> Optional[Credentials]:
        """
        Retrieves user credentials from token file or refreshes them if expired.
        """
        creds = None
        if os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            except Exception as e:
                logger.error(f"Error loading credentials from user token file: {e}")

        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Update saved credentials
                with open(self.token_path, "w") as token_file:
                    token_file.write(creds.to_json())
            except Exception as e:
                logger.error(f"Failed to refresh Google OAuth token: {e}")
                creds = None

        return creds

    def is_authenticated(self) -> bool:
        """
        Returns True if the user has valid credentials.
        """
        creds = self.get_credentials()
        return creds is not None and creds.valid

    def get_authorization_url(self, trip_id: str) -> str:
        """
        Generates OAuth 2.0 authorization URL, passing trip_id as state.
        """
        client_config = self._get_client_config()
        redirect_uri = client_config["web"]["redirect_uris"][0]
        
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=trip_id,
            prompt='consent'
        )
        return authorization_url

    def save_credentials_from_code(self, code: str) -> None:
        """
        Exchanges code for credentials and saves them to the user token file.
        """
        client_config = self._get_client_config()
        redirect_uri = client_config["web"]["redirect_uris"][0]
        
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
        flow.fetch_token(code=code)
        creds = flow.credentials
        
        with open(self.token_path, "w") as token_file:
            token_file.write(creds.to_json())

    def get_calendar_service(self) -> Any:
        """
        Builds and returns Google Calendar API client service.
        """
        creds = self.get_credentials()
        if not creds:
            raise PermissionError("User is not authenticated with Google Calendar")
        return build('calendar', 'v3', credentials=creds)

    def create_event(self, event_body: Dict[str, Any]) -> str:
        """
        Creates an event in the primary Google Calendar and returns the Google event ID.
        """
        service = self.get_calendar_service()
        event = service.events().insert(calendarId='primary', body=event_body).execute()
        return event.get('id')

    def update_event(self, event_id: str, event_body: Dict[str, Any]) -> None:
        """
        Updates an existing event in the primary Google Calendar.
        """
        service = self.get_calendar_service()
        service.events().update(calendarId='primary', eventId=event_id, body=event_body).execute()

    def delete_event(self, event_id: str) -> None:
        """
        Deletes an event from the primary Google Calendar.
        """
        service = self.get_calendar_service()
        try:
            service.events().delete(calendarId='primary', eventId=event_id).execute()
        except Exception as e:
            logger.error(f"Error deleting Google Calendar event {event_id}: {e}")
            raise e
