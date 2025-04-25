import os
import json
import logging
import requests
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,  # Note the lowercase 'filters'
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load credentials from JSON file
CREDENTIALS_FILE = "credentials.json"

def load_credentials():
    if not os.path.exists(CREDENTIALS_FILE):
        logger.error(f"Credentials file '{CREDENTIALS_FILE}' not found.")
        raise FileNotFoundError(f"Credentials file '{CREDENTIALS_FILE}' not found.")
    with open(CREDENTIALS_FILE, "r") as f:
        logger.info("Credentials loaded successfully.")
        return json.load(f)

# Load credentials into a global variable
credentials = load_credentials()

# Handler for /start command
async def start(update: Update, context):
    logger.info("Received /start command.")
    await update.message.reply_text(
        "Welcome!\n"
        "Use /post <site> <title> | <content> to create a post.\n"
        "Example: /post site1 My New Post | This is the content of my new post.\n\n"
        "Or use /upload <site> <title> and attach a Markdown file."
    )

# Handler for /upload command (for Markdown files)
#async def upload(update: Update, context):
    #logger.info("Received /upload command.")
    #try:
        ## Check if a file was sent
        #if not update.message.document:
            #logger.warning("No file attached to /upload command.")
            #await update.message.reply_text("Please attach a Markdown file with the command.")
            #return

        ## Extract the command and arguments from the caption
        #caption = update.message.caption
        #if not caption or not caption.startswith("/upload"):
            #logger.warning("Invalid caption. Use '/upload <site> <title>' as the caption.")
            #await update.message.reply_text(
                #"Please use '/upload <site> <title>' as the caption for the attached file."
            #)
            #return

        ## Parse arguments from the caption
        #parts = caption.split(maxsplit=2)  # Split into ['/upload', 'site', 'title']
        #if len(parts) < 3:
            #logger.warning("Insufficient arguments provided for /upload command.")
            #await update.message.reply_text(
                #"Usage: /upload <site> <title>\n"
                #"Attach a Markdown file with the command."
            #)
            #return

        #_, site, title = parts  # Unpack the parts

        ## Download the file
        #file_id = update.message.document.file_id
        #file = await context.bot.get_file(file_id)
        #file_extension = os.path.splitext(update.message.document.file_name)[-1]
        #file_path = f"{file_id}{file_extension}"
        #await file.download_to_drive(file_path)
        #logger.info(f"File downloaded successfully: '{file_path}'.")

        ## Send the file to WordPress
        #result = send_to_wordpress(site, title=title, markdown_file=file_path)

        ## Clean up the temporary file
        #os.remove(file_path)
        #logger.info(f"Temporary file deleted: '{file_path}'.")

        ## Respond to the user
        #if "error" in result:
            #logger.error(f"Error from WordPress API: {result['error']}")
            #await update.message.reply_text(f"Error: {result['error']}")
        #else:
            #logger.info(f"Post created successfully on site '{site}'. Post ID: {result.get('post_id')}")
            #await update.message.reply_text(f"Post created successfully!\nPost ID: {result.get('post_id')}")

    #except Exception as e:
        #logger.error(f"An error occurred while processing /upload command: {str(e)}")
        #await update.message.reply_text(f"An error occurred: {str(e)}")

async def upload(update: Update, context):
    logger.info("Received /upload command.")
    try:
        # Check if a file was sent
        if not update.message.document:
            logger.warning("No file attached to /upload command.")
            await update.message.reply_text("Please attach a Markdown file with the command.")
            return

        # Extract the command and arguments from the caption
        caption = update.message.caption
        if not caption or not caption.startswith("/upload"):
            logger.warning("Invalid caption. Use '/upload <site> <title>' as the caption.")
            await update.message.reply_text(
                "Please use '/upload <site> <title>' as the caption for the attached file."
            )
            return

        # Parse arguments from the caption

        parts = caption.split(maxsplit=2)  # Split into ['/upload', 'site', 'title']
        if len(parts) < 3:
            logger.warning("Insufficient arguments provided for /upload command.")
            await update.message.reply_text(
                "Usage: /upload <site> <title>\n"
                "Attach a Markdown file with the command."
            )
            return

        _, site, title = parts  # Unpack the parts
        logger.info("------------------------------------------------------")
        logger.info(title)
        logger.info("------------------------------------------------------")

        # Optional: Clean up the title by removing unwanted trailing text (e.g., "md file")
        #title = title.split(" md")[0].strip()  # Remove anything after " md" if present

        # Download the file
        file_id = update.message.document.file_id
        file = await context.bot.get_file(file_id)
        file_extension = os.path.splitext(update.message.document.file_name)[-1]
        file_path = f"{file_id}{file_extension}"
        await file.download_to_drive(file_path)
        logger.info(f"File downloaded successfully: '{file_path}'.")

        # Send the file to WordPress
        result = send_to_wordpress(site, title=title, markdown_file=file_path)

        # Clean up the temporary file
        os.remove(file_path)
        logger.info(f"Temporary file deleted: '{file_path}'.")

        # Respond to the user
        if "error" in result:
            logger.error(f"Error from WordPress API: {result['error']}")
            await update.message.reply_text(f"Error: {result['error']}")
        else:
            logger.info(f"Post created successfully on site '{site}'. Post ID: {result.get('post_id')}")
            await update.message.reply_text(f"Post created successfully!\nPost ID: {result.get('post_id')}")

    except Exception as e:
        logger.error(f"An error occurred while processing /upload command: {str(e)}")
        await update.message.reply_text(f"An error occurred: {str(e)}")

# Handler for /post command (for plain text content)
async def post(update: Update, context):
    logger.info("Received /post command.")
    try:
        # Parse arguments
        args = context.args
        if len(args) < 3:
            logger.warning("Insufficient arguments provided for /post command.")
            await update.message.reply_text(
                "Usage: /post <site> <title> | <content>\n"
                "Example: /post site1 My New Post | This is the content."
            )
            return

        site = args[0]
        combined_title_content = " ".join(args[1:])  # Combine all remaining arguments

        # Split title and content using the delimiter "|"
        if "|" not in combined_title_content:
            logger.warning("Delimiter '|' not found in the input.")
            await update.message.reply_text(
                "Please separate the title and content with '|'.\n"
                "Example: /post site1 My New Post | This is the content."
            )
            return

        title, content = map(str.strip, combined_title_content.split("|", 1))

        # Log the received data
        logger.info(f"Creating post:\nSite: {site}\nTitle: {title}\nContent: {content}")

        # Send the plain text content to WordPress
        result = send_to_wordpress(site, title=title, content=content)

        # Respond to the user
        if "error" in result:
            logger.error(f"Error from WordPress API: {result['error']}")
            await update.message.reply_text(f"Error: {result['error']}")
        else:
            logger.info(f"Post created successfully on site '{site}'. Post ID: {result.get('post_id')}")
            await update.message.reply_text(f"Post created successfully!\nPost ID: {result.get('post_id')}")

    except Exception as e:
        logger.error(f"An error occurred while processing /post command: {str(e)}")
        await update.message.reply_text(f"An error occurred: {str(e)}")

# Function to send data to WordPress
def send_to_wordpress(site, title, markdown_file=None, content=None):
    """
    Sends a post to WordPress.
    Handles both Markdown file uploads and plain text content.
    """
    site_config = credentials.get(site)
    if not site_config:
        return {"error": f"Site '{site}' not found in credentials."}

    base_url = site_config["base_url"]
    auth_method = site_config["auth_method"]

    # Prepare headers and authentication
    headers = {}
    if auth_method == "basic":
        username = site_config["username"]
        password = site_config["password"]
        auth = (username, password)
    elif auth_method == "jwt":
        token = site_config["token"]
        headers["Authorization"] = f"Bearer {token}"
        auth = None
    else:
        return {"error": f"Unsupported auth method '{auth_method}' for site '{site}'."}

    # Handle Markdown file upload
    if markdown_file:
        try:
            with open(markdown_file, "r", encoding="utf-8") as f:
                markdown_content = f.read()
            logger.info(f"Markdown file '{markdown_file}' read successfully.")
            # Convert Markdown to HTML (optional: use a library like markdown2)
            html_content = markdown_content  # Replace with actual Markdown-to-HTML conversion if needed

            # Send the request to the WordPress REST API
            url = f"{base_url}/wp-json/markdown-post-creator/v1/upload-markdown"

            # Prepare the files and data separately
            files = {
                "markdown_file": (os.path.basename(markdown_file), open(markdown_file, "rb")),
            }
            data = {
                "title": title,  # Send title as form-data
            }

            response = requests.post(url, headers=headers, auth=auth, files=files, data=data)
            logger.info(f"Response from WordPress API: {response.status_code} - {response.text}")
            return response.json()

        except Exception as e:
            logger.error(f"Failed to read Markdown file: {str(e)}")
            return {"error": f"Failed to read Markdown file: {str(e)}"}

            #with open(markdown_file, "r", encoding="utf-8") as f:
                #markdown_content = f.read()
            #logger.info(f"Markdown file '{markdown_file}' read successfully.")
            ## Convert Markdown to HTML (optional: use a library like markdown2)
            #html_content = markdown_content  # Replace with actual Markdown-to-HTML conversion if needed
        #except Exception as e:
            #logger.error(f"Failed to read Markdown file: {str(e)}")
            #return {"error": f"Failed to read Markdown file: {str(e)}"}

        ## Send the request to the WordPress REST API
        #url = f"{base_url}/wp-json/markdown-post-creator/v1/upload-markdown"
        #files = {
            #"markdown_file": (os.path.basename(markdown_file), open(markdown_file, "rb")),
            #"title": (None, title),
        #}
        #response = requests.post(url, headers=headers, auth=auth, files=files)
        #logger.info(f"Response from WordPress API: {response.status_code} - {response.text}")
        #return response.json()

    # Handle plain text content
    elif content:
        url = f"{base_url}/wp-json/wp/v2/posts"
        data = {
            "title": title,
            "content": content,
            "status": "publish",
        }
        response = requests.post(url, headers=headers, auth=auth, json=data)
        logger.info(f"Response from WordPress API: {response.status_code} - {response.text}")
        if response.status_code == 201:
            return {"status": "success", "message": "Post created successfully.", "post_id": response.json().get("id")}
        else:
            return {"error": f"Failed to create post: {response.text}"}

    # If neither Markdown file nor content is provided
    else:
        return {"error": "No Markdown file or content provided."}

# Main Function
def main():
    # Retrieve the Telegram Bot Token from an environment variable
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable is not set.")
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set.")

    logger.info("Starting Telegram bot.")
    application = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("post", post))
    application.add_handler(MessageHandler(filters.Document.ALL, upload))  # Filter for all documents

    # Start the bot
    application.run_polling()
    logger.info("Bot started successfully.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
