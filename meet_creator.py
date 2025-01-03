import os.path
from functools import partial

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.apps import meet_v2
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler


class MeetBot:
    SCOPES = ['https://www.googleapis.com/auth/meetings.space.created']

    def __init__(
            self,
            bot_token: str,
            google_secret_path: str = "client_secret.json",
            google_token_path: str = "token.json"
    ):
        self.secret_path = google_secret_path
        self.bot_token = bot_token
        self.google_token_path = google_token_path

        self.app = ApplicationBuilder().token(self.bot_token).build()
        self.app.add_handler(
            CommandHandler(["meet"], partial(self.create_space_handler, False)))
        self.app.add_handler(
            CommandHandler(["meetc"], partial(self.create_space_handler, True)))

        self.app.run_polling()

    def get_credentials(self):
        creds = None
        if os.path.exists(self.google_token_path):
            creds = Credentials.from_authorized_user_file(self.google_token_path, self.SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.secret_path, self.SCOPES)
                creds = flow.run_local_server(port=0)
            with open(self.google_token_path, 'w') as token:
                token.write(creds.to_json())
        return creds

    async def create_space(self, closed: bool = False):
        creds = self.get_credentials()
        space = None
        try:
            client = meet_v2.SpacesServiceAsyncClient(credentials=creds)
            if not closed:
                space={"config":{"access_type": "OPEN"}}
            request = meet_v2.CreateSpaceRequest(space=space)
            response = await client.create_space(request=request)
            return f'Space created: {response.meeting_uri}'
        except Exception as error:
            return f'An error occurred: {error}'

    async def create_space_handler(self, closed: bool, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = await self.create_space(closed)
        await update.message.reply_text(message)

if __name__ == '__main__':
    from bot_token import BOT_TOKEN

    google_secret_path = "client_secret.json"
    google_token_path = "token.json"

    MeetBot(BOT_TOKEN, google_secret_path, google_token_path)