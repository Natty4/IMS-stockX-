import os
import logging
import requests
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackContext,
    ConversationHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    ShippingQueryHandler,
    filters,
)

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define your bot token
BOT_TOKEN = os.getenv('BOT_TOKEN')
API_ENDPOINT = os.getenv('API_ENDPOINT')

# Define states for conversation handler
ADD_PRODUCT, ADD_PRODUCT_NAME, ADD_PRODUCT_CODE, ADD_PRODUCT_DESCRIPTION = range(4)
SALE, SALE_ITEM, SALE_QUANTITY = range(3)
STOCK, STOCK_ITEM, STOCK_QUANTITY = range(3)

# Handler for /start command
async def start(update: Update, context: CallbackContext) -> None:
    """Start the conversation and ask user to choose an action."""
    await update.message.reply_text(
        "Hi! I'm your stock management bot. Choose an action:\n"
        "/add - Add a new product\n"
        "/sale - Record a sale\n"
        "/stock - Manage stock"
    )

# Handler for /add command to start adding a new product
async def add_product(update: Update, context: CallbackContext) -> int:
    """Ask user to provide product name."""
    await update.message.reply_text(
        "Let's add a new product. Please enter the name of the product:"
    )
    return ADD_PRODUCT_NAME

# Function to handle capturing product name in conversation
async def add_product_name(update: Update, context: CallbackContext) -> int:
    """Store product name and ask for product code."""
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Enter the product code:")
    return ADD_PRODUCT_CODE

# Function to handle capturing product code in conversation
async def add_product_code(update: Update, context: CallbackContext) -> int:
    """Store product code and ask for product description."""
    context.user_data['code'] = update.message.text
    await update.message.reply_text("Enter the product description:")
    return ADD_PRODUCT_DESCRIPTION

# Function to complete adding a product
async def complete_add_product(update: Update, context: CallbackContext) -> None:
    """Complete adding product."""
    # Send API request to add the product using context.user_data
    product = context.user_data
    response = requests.post(f"{API_ENDPOINT}/products/", data=product)
    print(response, '----------------------------------------')
    await update.message.reply_text("Product added successfully!")
    return ConversationHandler.END

# Function to handle adding a product conversation cancellation
async def cancel_add_product(update: Update, context: CallbackContext) -> int:
    """Cancel adding product."""
    await update.message.reply_text("Adding product cancelled.")
    return ConversationHandler.END

# Handler for /sale command to record a sale
async def sale(update: Update, context: CallbackContext) -> int:
    """Ask user to provide item code and quantity sold."""
    await update.message.reply_text(
        "Enter the product code and quantity sold (e.g., ITEM_CODE1 QUANTITY1, ITEM_CODE2 QUANTITY2):"
    )
    return SALE_ITEM

# Function to handle capturing item code and quantity for sale
async def sale_process(update: Update, context: CallbackContext) -> None:
    """Record sale for each item."""
    items = update.message.text.split(",")
    for item in items:
        item_info = item.strip().split(" ")
        if len(item_info) == 2:
            product_code, quantity_sold = item_info
            # Send API request to record sale using product_code and quantity_sold
            response = requests.post(f"{API_ENDPOINT}/sales-transactions/", data={"product": product_code, "quantity_sold": quantity_sold})
            await update.message.reply_text(f"Sale recorded for {product_code}.")
        else:
            await update.message.reply_text("Invalid input format. Please provide input in the format: ITEM_CODE QUANTITY")
    return ConversationHandler.END

# Handler for /stock command to manage stock
async def stock(update: Update, context: CallbackContext) -> int:
    """Ask user to provide item code and quantity to manage stock."""
    await update.message.reply_text("Enter the product code:")
    return STOCK_ITEM

# Function to handle capturing item code and quantity for managing stock
async def stock_process(update: Update, context: CallbackContext) -> None:
    """Manage stock for the provided item."""
    product_code = update.message.text
    # Send API request to manage stock using product_code and quantity
    await update.message.reply_text(f"Stock managed for {product_code}.")
    return ConversationHandler.END

def main():
    """Start the bot."""
    # Create the application and pass the bot token to it
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Create a conversation handler for adding a product
    add_product_handler = ConversationHandler(
        entry_points=[CommandHandler("add", add_product)],
        states={
            ADD_PRODUCT_NAME: [MessageHandler(filters.TEXT, add_product_name)],
            ADD_PRODUCT_CODE: [MessageHandler(filters.TEXT, add_product_code)],
            ADD_PRODUCT_DESCRIPTION: [MessageHandler(filters.TEXT, complete_add_product)],
        },
        fallbacks=[CommandHandler("cancel", cancel_add_product)],
    )
    
    # Create a conversation handler for recording a sale
    sale_handler = ConversationHandler(
        entry_points=[CommandHandler("sale", sale)],
        states={SALE_ITEM: [MessageHandler(filters.TEXT, sale_process)]},
        fallbacks=[],
    )
    
    # Create a conversation handler for managing stock
    stock_handler = ConversationHandler(
        entry_points=[CommandHandler("stock", stock)],
        states={STOCK_ITEM: [MessageHandler(filters.TEXT, stock_process)]},
        fallbacks=[],
    )
    
    # Add the conversation handlers to the application
    application.add_handler(add_product_handler)
    application.add_handler(sale_handler)
    application.add_handler(stock_handler)
    
    # Add the /start command handler to the application
    application.add_handler(CommandHandler("start", start))
    
    # Start the application
    application.run_polling()
    
if __name__ == "__main__":
    main()
    