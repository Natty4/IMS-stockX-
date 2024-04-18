from collections import defaultdict
import os
import logging
import requests
import json
from PIL import Image
from typing import List
from tabulate import tabulate
from dotenv import load_dotenv
from telegram import InputMediaPhoto, Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackContext,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    ShippingQueryHandler,
    filters,   
)
from telegram.constants import ParseMode

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
ADD_PRODUCT, ADD_PRODUCT_NAME, ADD_PRODUCT_CODE, ADD_PRODUCT_DESCRIPTION, ADD_PRODUCT_PRICE_1, ADD_PRODUCT_PRICE_2, ADD_PRODUCT_QUANTITY, ADD_PRODUCT_IMAGE, ADD_PRODUCT_CATEGORY, ADD_PRODUCT_BRAND, ADD_PRODUCT_SIZE, ADD_PRODUCT_COLOR = range(12)
SALE_CATEGORY, SALE_PRODUCT_SELECTION, SALE_QUANTITY, SALE_CONFIRMATION = range(4)
STOCK_PRODUCT_SELECTION, STOCK_QUANTITY, ADD_NEW_STOCK_PRODUCT_SELECTION, ADD_NEW_STOCK_QUANTITY = range(4)
START, CHOOSE_ACTION, CREATE_STORE_NAME, CREATE_STORE_CONFIRM = range(4)

# Handler for /start command
async def start(update: Update, context: CallbackContext) -> None:
    """Start the conversation and ask user to choose an action."""
    
    # get user's detail from the update object (user_id, first_name, last_name, username, phone_number, language_code, location)
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name if update.effective_user.first_name else "N/A"
    last_name = update.effective_user.last_name if update.effective_user.last_name else "N/A"
    username = update.effective_user.username if update.effective_user.username else "N/A"
    
    user_store = requests.get(f"{API_ENDPOINT}/stores/")
    # Store the user's details in the context and database
    user = {
        "tg_id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "store": user_store.json()[0]["id"] if user_store.status_code == 200 else "N/A"
    }
    context.user_data['user'] = user
    
    # Check if the user already exists in the database
    
    
    await update.message.reply_text(
        f"Hello {first_name}! Welcome to the StockX Bot. How can I help you today?",
        reply_markup=ReplyKeyboardMarkup(
            [
                ["Add a Product", "Record a Sale"],
                ["Manage Stock", "Generate Reports"],
            ],
            resize_keyboard=True,
        ),
        
    )
# Define keyboard buttons
BUTTON_CREATE_STORE = "Create Store"
BUTTON_JOIN_STORE = "Join Store"
async def start(update: Update, context: CallbackContext):
    """Start the conversation and ask user to choose an action."""
    tg_id = str(update.effective_user.id)
    first_name = update.effective_user.first_name
    last_name = update.effective_user.last_name
    username = update.effective_user.username

    # Check if the user is new to the bot
    user_data = await check_user(tg_id)
    if user_data:
        # User already exists, continue with regular actions
        context.user_data['user_id'] = user_data['id']
        keyboard = [
            [BUTTON_CREATE_STORE],
            [BUTTON_JOIN_STORE]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        await update.message.reply_text("Welcome back! Choose an action:", reply_markup=reply_markup)
        return CHOOSE_ACTION
    else:
        # create stockx user
        response = requests.post(f"{API_ENDPOINT}/stockxuser/create/", json={"tg_id": tg_id, "first_name": first_name, "last_name": last_name, "username": username})
    
        # User is new, prompt to choose between creating or joining a store
        await update.message.reply_text(
            f"Welcome, {first_name} {last_name} ({username})!\n"
            "You are new to this bot. Please choose an action:",
            reply_markup=ReplyKeyboardMarkup([[BUTTON_CREATE_STORE], [BUTTON_JOIN_STORE]], one_time_keyboard=True)
        )
        return START

async def check_user(tg_id):
    """Check if the user exists in the database."""
    response = requests.get(f"{API_ENDPOINT}/stockxusers/?tg_id={tg_id}")
    if response.status_code == 200:
        return response.json()
    else:
        return None

async def create_store(update: Update, context: CallbackContext):
    """Start the process of creating a store."""
    await update.message.reply_text("Please enter the name of your store:")
    return CREATE_STORE_NAME

async def create_store_name(update: Update, context: CallbackContext):
    """Handle the input of the store name."""
    store_name = update.message.text
    context.user_data['store_name'] = store_name
    await update.message.reply_text(f"Your store name is: {store_name}. Confirm to create the store?",
                                    reply_markup=ReplyKeyboardMarkup([['Yes', 'No']], one_time_keyboard=True))
    return CREATE_STORE_CONFIRM

async def create_store_confirm(update: Update, context: CallbackContext):
    """Handle the confirmation of store creation."""
    confirm = update.message.text.lower()
    if confirm == 'yes':
        # Create the store in the database
        tg_id = str(update.effective_user.id)
        user_data = await check_user(tg_id)
        if user_data:
            user_id = user_data['id']
            store_name = context.user_data['store_name']
            # Call the API to create the store
            response = requests.post(f"{API_ENDPOINT}/storeuser/create/", json={"role": "", "store": store_name, "user": user_id})
            if response.status_code == 200:
                await update.message.reply_text("Store created successfully!")
            else:
                await update.message.reply_text("Failed to create store.")
        else:
            await update.message.reply_text("User not found.")
    else:
        await update.message.reply_text("Store creation cancelled.")

    return ConversationHandler.END
    
async def start_slider(update: Update, context: CallbackContext):
    # Fetch data from the endpoint
    DEFAULT_IMAGE_URL = "https://simbakids.netlify.app/_nuxt/img/simbakidslogo.104a990.png"
    response = requests.get(f"{API_ENDPOINT}/stocks/")
    if response.status_code == 200:
        stocks = response.json()
    else:
        await update.message.reply_text("Failed to fetch product data.")
        return
    
    # Initialize lists to store image URLs and captions
    image_urls = []
    captions = []

    # Extract image URLs and captions from the fetched data
    for stock in stocks:
        product = stock.get('product', {})
        # Use default link if image URL is None
        image_url = img if (img := product.get('image_url')) else DEFAULT_IMAGE_URL
        image_urls.append(image_url)

        caption = f"Name: {product.get('name', 'N/A')}\n"
        caption += f"Code: {product.get('code', 'N/A')}\n"
        caption += f"Category: {product.get('category', {}).get('name', 'N/A')}\n"
        caption += f"Brand: {product.get('brand', {}).get('name', 'N/A')}\n"
        caption += f"Description: {product.get('description', 'N/A')}\n"
        caption += f"Initial Quantity: {product.get('initial_quantity', 'N/A')}\n"
        caption += f"Stock on Hand: {stock.get('stock_on_hand', 'N/A')}\n"
        
        caption += f"Colors: {', '.join([color['name'] for color in product.get('colors', [])])}\n"
        captions.append(caption)

    # Set initial index to 0 if not set
    current_index = context.user_data.get('current_index', 0)
    context.user_data['current_index'] = current_index

    # If the current index is not set or the command was triggered directly, send the first image
    if current_index == 0 or update.message:
        context.user_data['image_urls'] = image_urls
        context.user_data['captions'] = captions

        # Send the first image with inline navigation buttons
        await navigate_slider(update, context)
    else:
        # Send the first image with inline navigation buttons
        await navigate_slider(update, context)

async def navigate_slider(update: Update, context: CallbackContext):
    DEFAULT_IMAGE_URL = "https://simbakids.netlify.app/_nuxt/img/simbakidslogo.104a990.png"
    query = update.callback_query
    current_index = context.user_data.get('current_index', 0)
    image_urls = context.user_data.get('image_urls', [])
    captions = context.user_data.get('captions', [])  # List of captions for each image

    if query and query.data == 'prev':
        current_index = (current_index - 1) % len(image_urls)
    elif query and query.data == 'next':
        current_index = (current_index + 1) % len(image_urls)

    context.user_data['current_index'] = current_index

    # Update the inline keyboard based on the current index
    inline_keyboard = []
    if current_index > 0:
        inline_keyboard.append(InlineKeyboardButton("Previous", callback_data="prev"))
    if current_index < len(image_urls) - 1:
        inline_keyboard.append(InlineKeyboardButton("Next", callback_data="next"))

    reply_markup = InlineKeyboardMarkup([inline_keyboard])
    
    try:
        message = query.message
    except AttributeError:
        message = update.message
    
    # replay_photo if the message is sent by the user/first time
    try:
        # Edit the message if it's sent by the bot
        await query.message.edit_media(
            media=InputMediaPhoto(media=image_urls[current_index], caption=captions[current_index]),
            reply_markup=reply_markup
        )
    except AttributeError:
        await message.reply_photo(
            photo=image_urls[current_index],
            caption=captions[current_index],
            reply_markup=reply_markup
        )
              
        
# Handler for /add command to start adding a new product
async def start_add_product(update: Update, context: CallbackContext) -> int:
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

# Function to handle capturing product description in conversation
async def add_product_description(update: Update, context: CallbackContext) -> int:
    """Store product description and ask for product price 1."""
    context.user_data['description'] = update.message.text
    await update.message.reply_text("Enter the product cost price:")
    return ADD_PRODUCT_PRICE_1

# Function to handle capturing product price 1 in conversation
async def add_product_price_1(update: Update, context: CallbackContext) -> int:
    """Store product price 1 and ask for product price 2."""
    context.user_data['cost_price'] = update.message.text
    await update.message.reply_text("Enter the product selling price:")
    return ADD_PRODUCT_PRICE_2

# Function to handle capturing product price 2 in conversation
async def add_product_price_2(update: Update, context: CallbackContext) -> int:
    """Store product price 2 and ask for product product initial quantity."""
    context.user_data['selling_price'] = update.message.text
    await update.message.reply_text("Enter the product initial quantity: (or 0 to skip)")
    return ADD_PRODUCT_QUANTITY

async def add_product_quantity(update: Update, context: CallbackContext) -> int:
    """Store product quantity and ask for product image."""
    try:
        message = update.message
        context.user_data['quantity'] = message.text

        # Ask for image or offer a skip option
        reply_markup = ReplyKeyboardMarkup(
            [[KeyboardButton("Skip")]],
            resize_keyboard=True  # Ensures the keyboard is resized to fit the buttons
        )
        await message.reply_text("Enter the product image URL or click 'Skip' to continue without adding an image:", reply_markup=reply_markup)
        return ADD_PRODUCT_IMAGE
    except Exception as e:
        logger.error(f"Error while processing add_product_quantity: {e}")
        await message.reply_text("An error occurred while processing your request. Please try again later.")
        return ConversationHandler.END


# Function to handle capturing product image URL in conversation
async def add_product_image(update: Update, context: CallbackContext) -> int:
    """Store product image URL and ask for product category."""
    message = update.message
    try:
        message = update.message
        if message.text.lower() == 'skip':
            context.user_data['image_url'] = None
        elif message.effective_attachment:
            # Process the attachment and get its URL
            attachment = message.effective_attachment
            file_id = attachment.file_id
            file = context.bot.get_file(file_id)
            context.user_data['image_url'] = file.file_path
        elif message.text.startswith(('http://', 'https://')) and any(message.text.lower().endswith(ext) for ext in ('.jpg', '.jpeg', '.png')):
            # Check if the message is a valid image URL
            context.user_data['image_url'] = message.text
        else:
            # Prompt the user to provide a valid image URL or image file
            await message.reply_text("Please provide a valid image URL, send an image file, or press 'Skip' to continue without adding an image.")
            return ADD_PRODUCT_IMAGE
        
        # Remove the "Skip" button
        reply_markup = ReplyKeyboardRemove()
        msg = "Product image received successfully." if context.user_data['image_url'] else "No image provided."
        await message.reply_text(msg, reply_markup=reply_markup)
        message = update.message
        # Proceed with the conversation
        categories = requests.get(f"{API_ENDPOINT}/categories/").json()
        categories_keyboard = [
            [InlineKeyboardButton(category['name'], callback_data=category['id'])]
            for category in categories
        ]
        reply_markup = InlineKeyboardMarkup(categories_keyboard)
        await message.reply_text("Please choose a category:", reply_markup=reply_markup)
        return ADD_PRODUCT_CATEGORY
    except Exception as e:
        logger.error(f"Error while processing add_product_image: {e}")
        await message.reply_text("An error occurred while processing your request. Please try again later.")
        return ConversationHandler.END

# Function to handle capturing product category in conversation
async def add_product_category(update: Update, context: CallbackContext) -> int:
    """Store product category and ask for product brand."""
    category_id = update.callback_query.data
    context.user_data['category'] = category_id
    
    msg = (
        "Choose a brand:"
    )
    brands = requests.get(f"{API_ENDPOINT}/brands/").json()
    brands_keyboard = [
        [InlineKeyboardButton(brand['name'], callback_data=brand['id'])]
        for brand in brands
    ]
    reply_markup = InlineKeyboardMarkup(brands_keyboard)
    await update.callback_query.message.edit_text(msg, reply_markup=reply_markup)
    return ADD_PRODUCT_BRAND

# Function to handle capturing product brand in conversation
async def add_product_brand(update: Update, context: CallbackContext) -> int:
    """Store product brand and ask for product size."""
    brand_id = update.callback_query.data
    context.user_data['brand'] = brand_id
    
    msg = (
        "Choose Size Range:"
    )
    sizes = requests.get(f"{API_ENDPOINT}/size-ranges/").json()
    sizes_keyboard = [
        [InlineKeyboardButton(f"{size['name']}: {size['size_value']}" , callback_data=size['id'])]
        for size in sizes
    ]
    reply_markup = InlineKeyboardMarkup(sizes_keyboard)
    await update.callback_query.message.edit_text(msg, reply_markup=reply_markup)
    return ADD_PRODUCT_SIZE

async def add_product_size(update: Update, context: CallbackContext) -> int:
    """Store product size and ask for product color."""
    size_id = update.callback_query.data
    sizes = requests.get(f"{API_ENDPOINT}/size-ranges/").json()
    selected_size = None
    for size in sizes:
        if int(size['id']) == int(size_id):
            selected_size = size
            break
    
    if selected_size:
        context.user_data['size'] = selected_size
    else:
        logger.error(f"Size with ID {size_id} not found.")
    
    msg = (
            "Choose color (multiple selections allowed):"
           )
    colors = requests.get(f"{API_ENDPOINT}/colors/").json()
    colors_keyboard = [
        [InlineKeyboardButton(color['name'], callback_data=color['id'])]
        for color in colors
    ]
    reply_markup = InlineKeyboardMarkup(colors_keyboard)
    await update.callback_query.message.edit_text(msg, reply_markup=reply_markup)
    return ADD_PRODUCT_COLOR

async def add_product_color(update: Update, context: CallbackContext) -> int:
    """Store product color and continue the process."""
    color_id = update.callback_query.data
    user_data = context.user_data
    user_colors = context.user_data.get('colors', [])
    # Fetch colors from API endpoint
    colors = requests.get(f"{API_ENDPOINT}/colors/").json()
    msg = (
            "Choose color (multiple selections allowed):"
           )
    
    if 'colors' not in user_data:
        user_data['colors'] = []
    
    if color_id == 'done':
        # If 'done' button is clicked, complete the process
        del user_data['colors']  # Remove 'colors' key
        # Create the product using API
        try:
            product_data = {    
                'name': user_data['name'],
                'code': user_data['code'],
                'description': user_data['description'],
                'category': user_data['category'],
                'brand': user_data['brand'],
                'size_range': user_data['size']['id'],
                'colors': user_colors,
                'initial_quantity': user_data['quantity'],
                'cost_price': user_data['cost_price'],
                'selling_price': user_data['selling_price'],
                'image_url': user_data.get('image_url', ''),
                'store': user_data['user']['store'],  # 'store' is the ID of the store associated with the user
                'created_by': update.callback_query.message.chat.username
            }
            response = requests.post(f"{API_ENDPOINT}/products/create/", json=product_data)
            if response.status_code == 201:
                # Product created successfully
                product_details = "\n".join([f"{key}: {value}" for key, value in product_data.items() if key != 'colors'])
                colors_list = ", ".join(user_colors)
                response_text = f"✅ Product added successfully!\n\n{product_details}\n\nColors: {colors_list}\n\nResponse from API: {response.status_code} "
                await update.callback_query.message.edit_text(response_text)
                return ConversationHandler.END
            else:
                # Failed to create Remove the inline keyboard and accompanying text after displaying the response
                await update.callback_query.message.edit_text(f"❌ Faild!  to add product. Error: {response.status_code} {response.json()}")
                
                return ConversationHandler.END
        except Exception as e:
            logger.error(f"Error while creating product: {e}")
            await update.callback_query.message.edit_text("An error occurred while adding the product. Please try again later.")
            # Remove the inline keyboard and accompanying text after displaying the response
            await update.callback_query.message.edit_text("Faild!")
            await update.callback_query.message.edit_reply_markup(reply_markup=None)
            return ConversationHandler.END
        
        
    
    # Toggle color selection
    if color_id in user_colors:
        user_colors.remove(color_id)
    else:
        user_colors.append(color_id)
    
    context.user_data['colors'] = user_colors
    
    colors_keyboard = [
        [InlineKeyboardButton(f"{color['name']} {'✅' if str(color['id']) in user_colors else ''}", callback_data=color['id'])]
        for color in colors
    ]
    
    colors_keyboard.append([InlineKeyboardButton("Done", callback_data="done")])
    reply_markup = InlineKeyboardMarkup(colors_keyboard)
    
    # Check if the reply markup needs to be edited
    if update.callback_query.message.reply_markup != reply_markup:
        await update.callback_query.message.edit_text(msg, reply_markup=reply_markup)
    
    return ADD_PRODUCT_COLOR

# Function to handle adding a product conversation cancellation
async def cancel_add_product(update: Update, context: CallbackContext) -> int:
    """Cancel adding product."""
    context.user_data.pop('name', None)
    context.user_data.pop('code', None)
    context.user_data.pop('description', None)
    context.user_data.pop('cost_price', None)
    context.user_data.pop('selling_price', None)
    context.user_data.pop('quantity', None)
    context.user_data.pop('image_url', None)
    context.user_data.pop('category', None)
    context.user_data.pop('brand', None)
    context.user_data.pop('size', None)
    context.user_data.pop('colors', None)
    
    await update.message.reply_text("Adding product cancelled.")
    return ConversationHandler.END

# Function to start the sale conversation
async def start_sale(update: Update, context: CallbackContext) -> int:
    """Start the sale conversation and prompt user to choose a category."""
    try:
        # Fetch categories from the API
        categories = requests.get(f"{API_ENDPOINT}/categories/").json()
        
        # Create a list of InlineKeyboardButtons for categories
        category_buttons = [
            [InlineKeyboardButton(category['name'], callback_data=str(category['id']))]
            for category in categories
        ]
        
        # Create the reply markup
        reply_markup = InlineKeyboardMarkup(category_buttons)
        
        # Send message with the category list and inline buttons
        await update.message.reply_text("Select a category:", reply_markup=reply_markup)
        
        return SALE_CATEGORY
    except Exception as e:
        logger.error(f"Error in starting sale conversation: {e}")
        await update.message.edit_text("An error occurred. Please try again later.")
        return ConversationHandler.END

async def select_sale_category(update: Update, context: CallbackContext) -> int:
    """Fetch and show products for the selected category."""
    query = update.callback_query
    category_id = int(query.data)
    try:
        # Fetch products belonging to the selected category from the API
        # response = requests.get(f"{API_ENDPOINT}/categories/{category_id}/products/")
        response = requests.get(f"{API_ENDPOINT}/stocks/")

        response.raise_for_status()  # Raise an error for non-2xx status codes
        products = []
        
        for pro in response.json():
            if pro['product']['category']['id'] == category_id:
                products.append(pro['product'])        
        # Store products in the given category in user_data for further processing
        context.user_data['products'] = products
        
        # Store the selected category in user_data for further processing
        context.user_data['selected_category'] = category_id
        
        # Store the product list in user_data for further processing
        context.user_data['selected_products'] = []
        
        # Create a list of InlineKeyboardButtons for products
        product_buttons = [
            [InlineKeyboardButton(f"{product['name']} - {product['code']}", callback_data=str(product['id']))]
            for product in products
        ]
        
        # Add a "Done" button at the end
        product_buttons.append([InlineKeyboardButton("Done", callback_data="done")])
        
        # Create the reply markup
        reply_markup = InlineKeyboardMarkup(product_buttons)
        
        # Edit the message to show the product list and inline buttons
        await query.message.edit_text("Select products to record a sale:", reply_markup=reply_markup)
        
        return SALE_PRODUCT_SELECTION
    except Exception as e:
        logger.error(f"Error fetching products for category {category_id}: {e}")
        await query.message.reply_text("An error occurred while fetching products. Please try again later.")
        context.user_data.pop('products', None)
        context.user_data.pop('selected_category', None)
        context.user_data.pop('selected_products', None)
        return ConversationHandler.END

async def select_sale_product(update: Update, context: CallbackContext) -> int:
    """Process product selection for sale."""
    query = update.callback_query
    selected_products = context.user_data.get('selected_products', [])
    products = context.user_data.get('products', [])
    
    if query.data == "done":
        if selected_products:
            response_data = [product['name'] + " - " + product['code'] for product in selected_products]
            response = "You have selected the following products:\n\n" + "\n\n".join(response_data) + f"\n\nPlease enter the quantity for each product one by one"
            #Remove inline keyboard after selection is done and show the selected products
            await query.message.edit_text(response)
            await update.callback_query.message.reply_text(f"Enter quantity for {selected_products[0]['name']} - {selected_products[0]['code']}:")
            return SALE_QUANTITY
        else:
            await update.callback_query.message.edit_text("No products selected.")
            context.user_data.pop('products', None)
            context.user_data.pop('selected_category', None)
            context.user_data.pop('selected_products', None)
            return ConversationHandler.END
    else:
        # If a product is selected, add it to the list
        product_id = int(query.data)
        product = next((p for p in products if p['id'] == product_id), None)
        
        if product:
            if product in selected_products:
                # If the product is already selected, remove it
                selected_products.remove(product)
            else:
                # If the product is not selected, add it
                selected_products.append(product)
            
            # Show the updated product list with selection status
            product_buttons = [
                [
                    InlineKeyboardButton(
                        f"{p['name']} - {p['code']} {'✅' if p in selected_products else ''}",
                        callback_data=str(p['id'])
                    )
                ]
                for p in products
            ]
            product_buttons.append([InlineKeyboardButton("Done 🆗", callback_data="done")])
            reply_markup = InlineKeyboardMarkup(product_buttons)
            
            await query.message.edit_reply_markup(reply_markup=reply_markup)
            return SALE_PRODUCT_SELECTION
        else:
            await query.answer("Invalid product selection.")
            context.user_data.pop('products', None)
            context.user_data.pop('selected_category', None)
            context.user_data.pop('selected_products', None)
            return ConversationHandler.END

async def select_sale_quantity(update: Update, context: CallbackContext) -> int:
    """Process product quantity for sale."""
    quantity = update.message.text
    # Process the quantity input and proceed to the next product or finalize the sale
    # Here you can add your logic to process the quantity and update the sale information
    # For demonstration purposes, let's assume we're just storing the quantities in user_data
    selected_products = context.user_data.get('selected_products', [])
    selected_products_quantities = context.user_data.get('selected_products_quantities', {})
    product = selected_products[0]  # Get the first product in the list
    selected_products_quantities[product['id']] = quantity
    context.user_data['selected_products_quantities'] = selected_products_quantities
    selected_products.pop(0)  # Remove the processed product from the list
    
    if selected_products:
        # If there are more products, prompt the user to enter quantity for the next product
        product = selected_products[0]
        await update.message.reply_text(f"Enter quantity for {product['name']} - {product['code']}:")
        return SALE_QUANTITY
    else:
        # If all products have quantities, proceed to finalize the sale
        confirmation_keyboard = [
            [InlineKeyboardButton("Confirm Sale", callback_data="confirm")],
            [InlineKeyboardButton("Cancel Sale", callback_data="cancel")]
        ]
        reply_markupa = InlineKeyboardMarkup(confirmation_keyboard)
        
        await update.message.reply_text("All quantities provided. Proceeding to finalize the sale.", reply_markup=reply_markupa)
        return SALE_CONFIRMATION

async def finalize_sale(update: Update, context: CallbackContext) -> int:
    """Finalize the sale."""
    query = update.callback_query
    if query.data == "cancel":
        # Remove the inline keyboard and replace the message with a cancellation message if the sale is cancelled and end the conversation
        await query.message.edit_text("Sale cancelled.")
        # await update.callback_query.message.reply_text("Sale cancelled.")
        context.user_data.pop('products', None)
        context.user_data.pop('selected_category', None)
        context.user_data.pop('selected_products', None)
        context.user_data.pop('selected_products_quantities', None)
        return ConversationHandler.END
    
    # Generate the JSON object appropriate for the POST request
    selected_products_quantities = context.user_data.get('selected_products_quantities', {})
    sale_data = {
        "products": [
            {"product_id": product_id, "quantity": quantity}
            for product_id, quantity in selected_products_quantities.items()
        ]
    }
    
    """
   {'quantity_sold': ['This field is required.'], 'soled_by': ['This field is required.'], 'product': ['This field is required.']}
    
    """
    
    for product_id, quantity in selected_products_quantities.items():
        sale_data['quantity_sold'] = quantity
        sale_data['sold_by'] = update.callback_query.message.chat.username
        sale_data['product'] = product_id
        sale_data['store'] = context.user_data['user']['store']
        response = requests.post(f"{API_ENDPOINT}/sales/create/", json=sale_data)
        if response.status_code == 201:
            await update.callback_query.message.reply_text(f"✅ Sale recorded for {product_id}.")
        else:
            await update.callback_query.message.reply_text(f"❌ Failed to record sale for {product_id}. Error: {response.status_code} {response.json()}")
    # Example: Send a POST request with the sale data
    # response = requests.post(f"{API_ENDPOINT}/sales/create/", json=sale_data)
    # Handle the response accordingly
    
    # Remove the inline keyboard and replace the message with a success message and end the conversation
    await query.message.edit_text("Sale finalized successfully.")
    # await update.callback_query.message.reply_text()
    context.user_data.pop('selected_products', None)
    context.user_data.pop('products', None)
    context.user_data.pop('selected_category', None)
    context.user_data.pop('selected_products_quantities', None)
    
    return ConversationHandler.END

# Function to handle cancellation of the sale conversation
async def cancel_sale(update: Update, context: CallbackContext) -> int:
    """Cancel the sale conversation."""
    await update.message.reply_text("Sale cancelled.")
    context.user_data.pop('selected_products', None)
    context.user_data.pop('products', None)
    context.user_data.pop('selected_category', None)
    context.user_data.pop('selected_products_quantities', None)
    return ConversationHandler.END



# Function to start the stock update conversation
async def start_stock_update(update: Update, context: CallbackContext) -> int:
    """Start the stock update conversation and prompt user to choose a product."""
    try:
        user = context.user_data['user']
        # Fetch products along with their current stock on hand quantities from the API
        stocks = requests.get(f"{API_ENDPOINT}/stocks/", data=user).json()
        
        # Extract product information from each stock entry
        products = [
            {
                'id': stock['product']['id'],
                'name': stock['product']['name'],
                'code': stock['product']['code'],
                'stock_on_hand': stock['stock_on_hand']
            }
            for stock in stocks
        ]
        stock_dic = {}
        for product in products:
            stock_dic[product['id']] = product
        context.user_data['stocks'] = stock_dic
        # Create a list of InlineKeyboardButtons for products
        product_buttons = [
            [InlineKeyboardButton(f"{product['name']} - {product['code']} ({product['stock_on_hand']} on hand)", callback_data=str(product['id']))]
            for product in products
        ]
        # Add option to add new stock
        product_buttons.append([InlineKeyboardButton("Add New Stock", callback_data="add_new_stock")])
        # Create the reply markup
        reply_markup = InlineKeyboardMarkup(product_buttons)
        # Send message with the product list and inline buttons
        await update.message.reply_text("Select a product to update stock quantity:", reply_markup=reply_markup)
        return STOCK_PRODUCT_SELECTION
    except Exception as e:
        logger.error(f"Error in starting stock update conversation: {e}")
        await update.message.reply_text("An error occurred. Please try again later.")
        context.user_data.pop('stocks', None)
        return ConversationHandler.END


# Function to handle selection of a product
async def select_stock_product(update: Update, context: CallbackContext) -> int:
    """Store the selected product and prompt user to enter quantity."""
    query = update.callback_query
    product_id = query.data
    udata = context.user_data['user']
    if product_id == "add_new_stock":
        # Add new stock option selected, prompt user to select a product from the list of all products
        try:
            # Fetch all products from the products enpoint and from stocks endpoint then pick the ones that are not in stocks
            products = requests.get(f"{API_ENDPOINT}/products/", data=udata).json()
            stocks = requests.get(f"{API_ENDPOINT}/stocks/", data=udata).json()
            # generate new products dict from the products list and stocks list thar are not in stocks
            new_products = [product for product in products if product['id'] not in [stock['product']['id'] for stock in stocks]]
            # if there are no new products, go to the else block instead of ending the conversation
            if not new_products:
                await query.message.edit_text("No products found to add new stock.")
                return ConversationHandler.END
            product_buttons = [
                [InlineKeyboardButton(f"{product['name']}-{product['code']}", callback_data=str(product['id']))]
                for product in new_products
            ]
            # Create the reply markup
            reply_markup = InlineKeyboardMarkup(product_buttons)
            # Edit message to show list of all products for adding new stock
            await query.message.edit_text("Select a product to add new stock:", reply_markup=reply_markup)
            return ADD_NEW_STOCK_PRODUCT_SELECTION
        except Exception as e:
            logger.error(f"Error fetching products: {e}")
            await query.message.reply_text("An error occurred. Please try again later.")
            return ConversationHandler.END
    else:
        try:
            # Fetch the selected product details from the user_data
            product_details = context.user_data['stocks'][int(product_id)]
            # Store the selected product details in user_data for further processing
            context.user_data['selected_product'] = product_details
            # Remove the inline keyboard and Prompt the user to enter the quantity
            await query.message.edit_text(f"Enter the quantity to update the stock for the selected product:\n{product_details['name']} - {product_details['code']}")
            return STOCK_QUANTITY
        except Exception as e:
            logger.error(f"Error fetching product details for product {product_id}: {e}")
            await query.message.edit_text("An error occurred while fetching product details. Please try again later.")
            context.user_data.pop('selected_product', None)
            context.user_data.pop('stocks', None)
            return ConversationHandler.END


# Function to handle the quantity input
async def update_stock_quantity(update: Update, context: CallbackContext) -> int:
    """Process the quantity input and update the stock."""
    quantity = update.message.text
    selected_product = context.user_data.get('selected_product')
    udata = context.user_data['user']
    if not selected_product:
        await update.message.reply_text("No product selected. Please start again.")
        context.user_data.pop('selected_product', None)
        context.user_data.pop('stocks', None)
        return ConversationHandler.END
    try:
        # Prepare the data to update stock
        stock_update_data = {
            "stock_on_hand": int(quantity),
            "product": selected_product['id'],
            "created_by": update.message.from_user.username,
            "user": udata
        }
        # Update stock using the API
        response = requests.put(f"{API_ENDPOINT}/stocks/update/", json=stock_update_data)
        
        if response.status_code == 200:
            updated_stock = response.json()
            await update.message.reply_text(f"✅ Stock updated successfully. \nTotal on hand quantity for {selected_product['name']} - {selected_product['code']}: {updated_stock['stock_on_hand']}")
        else:
            await update.message.reply_text(f"❌ Failed to update stock. Error: {response.status_code} {response.json()}")
        
    except Exception as e:
        logger.error(f"Error updating stock for product {selected_product['id']}: {e}")
        await update.message.reply_text("An error occurred while updating stock. Please try again later.")
    context.user_data.pop('selected_product', None)
    context.user_data.pop('stocks', None)
    return ConversationHandler.END


# Function to handle selection of a product for adding new stock
async def add_new_stock(update: Update, context: CallbackContext) -> int:
    """Store the selected product for adding new stock."""
    query = update.callback_query
    product_id = int(query.data)
    try:
        # Fetch the selected product details from the API
        product_details = requests.get(f"{API_ENDPOINT}/products/{product_id}/").json()
        # Store the selected product details in user_data for further processing
        context.user_data['selected_product'] = product_details
        # Prompt the user to enter the quantity for adding new stock
        await query.message.edit_text(f"Enter the quantity to add new stock for the selected product:\n{product_details['name']} - {product_details['code']}")
        return ADD_NEW_STOCK_QUANTITY
    except Exception as e:
        logger.error(f"Error fetching product details for product {product_id}: {e}")
        await query.message.edit_text("An error occurred while fetching product details. Please try again later.")
        context.user_data.pop('selected_product', None)
        return ConversationHandler.END


# Function to handle the quantity input for adding new stock
async def add_new_stock_quantity(update: Update, context: CallbackContext) -> int:
    """Process the quantity input and add new stock."""
    quantity = update.message.text
    selected_product = context.user_data.get('selected_product')
    
    if not selected_product:
        await update.message.reply_text("No product selected. Please start again.")
        context.user_data.pop('selected_product', None)
        return ConversationHandler.END
    try:
        # Prepare the data to add new stock
        stock_data = {
            "stock_on_hand": int(quantity),
            "low_stock_threshold": selected_product['low_stock_threshold'],  # You may adjust this if needed
            "created_by": update.message.from_user.username,
            "product": selected_product['id'],
            "store": context.user_data['user']['store']
        }
        # Add new stock using the API
        response = requests.post(f"{API_ENDPOINT}/stocks/create/", json=stock_data)
        if response.status_code == 201:
            new_stock = response.json()
            await update.message.reply_text(f"✅ New stock added successfully. \nTotal on hand quantity for {selected_product['name']} - {selected_product['code']}: {new_stock['stock_on_hand']}")
        else:
            await update.message.reply_text(f"❌ Failed to add new stock. Error: {response.status_code} {response.json()}")
        
    except Exception as e:
        logger.error(f"Error adding new stock for product {selected_product['id']}: {e}")
        await update.message.reply_text("An error occurred while adding new stock. Please try again later.")
    context.user_data.pop('selected_product', None)
    return ConversationHandler.END


# Function to handle cancellation of the conversation
async def cancel_stock_update(update: Update, context: CallbackContext) -> int:
    """Cancel the stock update conversation."""
    await update.message.reply_text("Stock update cancelled.")
    context.user_data.pop('selected_product', None)
    context.user_data.pop('stocks', None)
    return ConversationHandler.END
    

import matplotlib.pyplot as plt
import numpy as np
import io
from datetime import datetime, timedelta

def generate_bar_chart(report_data):
    labels = ['Stock In', 'Stock Out', 'Stock On Hand']
    values = [report_data['total_stock_in'], report_data['total_stock_out'] * -1, report_data['total_stock_on_hand']]

    # Define custom colors for the bars
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

    # Create a bar chart to visualize the stock in, stock out, and stock on hand data
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(labels))
    bars = ax.bar(x, values, color=colors)
    ax.set_xlabel('Stock Type')
    ax.set_ylabel('Quantity')
    ax.set_title('Total Stock In vs Stock Out vs Stock On Hand')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)

    # Add the data labels on top of the bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height + 10, str(height), ha='center', va='bottom')

    # Save the bar chart visualization as bytes in memory
    buf_bar = io.BytesIO()
    plt.savefig(buf_bar, format='png')
    plt.close()  # Close the figure to free memory
    buf_bar.seek(0)

    return buf_bar


def generate_top_ten_products_bar_chart(sales_data):
    # Count the total quantity sold for each product
    product_sales = defaultdict(int)
    for transaction in sales_data:
        product_id = transaction['product']['code']
        quantity_sold = float(transaction['quantity_sold'])
        product_sales[product_id] += quantity_sold

    # Sort the products based on total quantity sold and select the top ten
    top_ten_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:10]
    product_ids, quantities_sold = zip(*top_ten_products)
    
    # Fetch product names from the API endpoint (assuming there's an endpoint to fetch product details)
    product_names = {}  # This dictionary should contain product names fetched from the API
    
    # Define custom colors for the bars
    colors = plt.cm.tab10(np.arange(len(product_ids)))

    # Create bar chart
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(product_ids, quantities_sold, tick_label=[product_names.get(product_id, f' {product_id} ') for product_id in product_ids], color=colors)
    ax.set_xlabel('Product')
    ax.set_ylabel('Total Quantity Sold')
    ax.set_title('Top Ten Products by Sales Quantity')
    ax.grid(True)
    plt.xticks(rotation=45)

    # Add the data labels on top of the bars
    for bar, quantity in zip(bars, quantities_sold):
        ax.text(bar.get_x() + bar.get_width() / 2, quantity + 10, str(quantity), ha='center', va='bottom')

    # Save the bar chart visualization as bytes in memory
    buf_bar_chart = io.BytesIO()
    plt.savefig(buf_bar_chart, format='png')
    plt.close()  # Close the figure to free memory
    buf_bar_chart.seek(0)

    return buf_bar_chart

      
       
def generate_stock_bar_charts(API_ENDPOINT):
    # Fetch data from the /stock-transactions/ endpoint
    stock_transactions_response = requests.get(f"{API_ENDPOINT}/stock-transactions/")
    stock_transactions = stock_transactions_response.json()

    # Fetch data from the /stocks-list/ endpoint
    stocks_list_response = requests.get(f"{API_ENDPOINT}/stocks/")
    stocks_list = stocks_list_response.json()

    # Group stock transactions by product
    stock_transactions_by_product = {}
    for transaction in stock_transactions:
        product_code = transaction['product']['code']
        if product_code not in stock_transactions_by_product:
            stock_transactions_by_product[product_code] = []
        stock_transactions_by_product[product_code].append(transaction)

    # Aggregate stock transactions to calculate stock in, stock out, and on-hand quantity for each product
    product_data = {}
    for stock_item in stocks_list:
        product_code = stock_item['product']['code']
        stock_in = 0
        stock_out = 0
        for transaction in stock_transactions_by_product.get(product_code, []):
            if transaction['stock_type'] == '1':  # Stock in
                stock_in += transaction['quantity']
            elif transaction['stock_type'] == '2':  # Stock out
                stock_out += abs(transaction['quantity'])  # Take absolute value for stock out
        stock_on_hand = stock_item['stock_on_hand']
        product_data[product_code] = {'stock_in': stock_in, 'stock_out': stock_out, 'stock_on_hand': stock_on_hand}

    # Prepare data for the grouped bar charts
    product_codes = list(product_data.keys())
    num_products = len(product_codes)

    # Determine the number of charts based on the number of products
    num_charts = max((num_products + 5) // 6, 1)  # Calculate the number of charts required, ensuring at least 1 chart

    # Generate charts for each group of products
    charts = []
    start_index = 0
    for i in range(num_charts):
        end_index = min(start_index + 6, num_products)  # Ensure end_index does not exceed num_products
        group_product_codes = product_codes[start_index:end_index]
        group_product_data = {code: product_data[code] for code in group_product_codes}

        # Prepare data for the grouped bar chart
        group_labels = [f'{code}' for code in group_product_codes]
        group_stock_in_values = [group_product_data[code]['stock_in'] for code in group_product_codes]
        group_stock_out_values = [group_product_data[code]['stock_out'] for code in group_product_codes]
        group_stock_on_hand_values = [group_product_data[code]['stock_on_hand'] for code in group_product_codes]

        # Plot the grouped bar chart for the current group
        fig, ax = plt.subplots()
        x = np.arange(len(group_labels))
        width = 0.2  # Width of each bar
        rects1 = ax.bar(x - width, group_stock_in_values, width, label='Stock In')
        rects2 = ax.bar(x, group_stock_out_values, width, label='Stock Out')
        rects3 = ax.bar(x + width, group_stock_on_hand_values, width, label='Stock On Hand')

        ax.set_xlabel('Product Code')
        ax.set_ylabel('Quantity')
        ax.set_title('Stock Transactions by Product')
        ax.set_xticks(x)
        ax.set_xticklabels(group_labels)
        ax.legend()

        plt.xticks(rotation=45)
        plt.tight_layout()

        # Annotate each bar with its respective value
        for rects in [rects1, rects2, rects3]:
            for rect in rects:
                height = rect.get_height()
                ax.annotate('{}'.format(height),
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom', rotation=90)  # Rotate the annotation text vertically

        # Save the plot as a PNG image
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        charts.append(buf)

        start_index += 6

    return charts



def generate_sales_time_series_chart(sales_data, start_date=None, end_date=None, product_codes=None):
    # If no filters are provided, use the entire sales dataset
    if start_date is None and end_date is None and product_codes is None:
        filtered_sales_data = sales_data
    else:
        # Apply filters to sales data
        filtered_sales_data = []
        for transaction in sales_data:
            transaction_date = datetime.strptime(transaction['created_at'][:10], '%Y-%m-%d')
            if (start_date is None or transaction_date >= start_date) and \
               (end_date is None or transaction_date <= end_date) and \
               (product_codes is None or transaction['product']['code'] in product_codes):
                filtered_sales_data.append(transaction)
        # Extract all unique product codes from filtered data
        product_codes = {transaction['product']['code'] for transaction in filtered_sales_data}

        # Create a dictionary to store sales data by product and date
        product_sales_by_date = {product_code: defaultdict(int) for product_code in product_codes}

        # Extract all unique dates and convert them to a sorted list
        all_dates = sorted(set(transaction['created_at'][:10] for transaction in filtered_sales_data))

        # Determine the earliest and latest dates
        earliest_date = min(all_dates)
        latest_date = max(all_dates)

        # Create a list of all dates between the earliest and latest date
        all_dates_full = [datetime.strptime(earliest_date, '%Y-%m-%d') + timedelta(days=i) for i in range((datetime.strptime(latest_date, '%Y-%m-%d') - datetime.strptime(earliest_date, '%Y-%m-%d')).days + 1)]
        all_dates_full = [date.strftime('%m-%d') for date in all_dates_full]

        # Initialize quantities sold for each date and product to 0
        for product_code in product_codes:
            for date in all_dates_full:
                product_sales_by_date[product_code][date] = 0

        # Populate the dictionary with actual sales data
        for transaction in filtered_sales_data:
            product_code = transaction['product']['code']
            date = transaction['created_at'][:10]  # Extracting only the date portion
            quantity_sold = int(transaction['quantity_sold'])
            product_sales_by_date[product_code][date] += quantity_sold

        # Plot a line chart for each product
        fig, ax = plt.subplots(figsize=(10, 6))
        for product_code, sales_by_date in product_sales_by_date.items():
            sales_for_product = []
            for date in all_dates_full:
                quantity = sales_by_date[date]
                sales_for_product.append(quantity)
                ax.scatter(date, quantity, color='#0ADD08')  # Display quantity sold as dots
                ax.annotate(quantity, (date, quantity), textcoords="offset points", xytext=(0,10), ha='center')  # Annotate the dot with quantity sold
            ax.plot(all_dates_full, sales_for_product, linestyle='-', label=f'Product {product_code}')

        ax.set_xlabel('Date')
        ax.set_ylabel('Quantity Sold')
        ax.set_title('Product Sales Over Time')
        ax.legend()
        ax.grid(True)
        plt.xticks(rotation=45)

        # Save the line chart visualization as bytes in memory
        buf_line_chart = io.BytesIO()
        plt.savefig(buf_line_chart, format='png')
        plt.close()  # Close the figure to free memory
        buf_line_chart.seek(0)

        return buf_line_chart

def generate_sales_time_series_chart(sales_data):
    # Extract all unique product codes
    product_codes = {transaction['product']['code'] for transaction in sales_data}

    # Create a dictionary to store sales data by product and date
    product_sales_by_date = {product_code: defaultdict(int) for product_code in product_codes}

    # Extract all unique dates and convert them to a sorted list
    all_dates = sorted(set(transaction['created_at'][:10] for transaction in sales_data))

    # Determine the earliest and latest dates
    earliest_date = min(all_dates)
    latest_date = max(all_dates)

    # Create a list of all dates between the earliest and latest date
    all_dates_full = [datetime.strptime(earliest_date, '%Y-%m-%d') + timedelta(days=i) for i in range((datetime.strptime(latest_date, '%Y-%m-%d') - datetime.strptime(earliest_date, '%Y-%m-%d')).days + 1)]
    all_dates_full = [date.strftime('%Y-%m-%d') for date in all_dates_full]

    # Initialize quantities sold for each date and product to 0
    for product_code in product_codes:
        for date in all_dates_full:
            product_sales_by_date[product_code][date] = 0

    # Populate the dictionary with actual sales data
    for transaction in sales_data:
        product_code = transaction['product']['code']
        date = transaction['created_at'][:10]  # Extracting only the date portion
        quantity_sold = int(transaction['quantity_sold'])
        product_sales_by_date[product_code][date] += quantity_sold

    # Plot a line chart for each product
    fig, ax = plt.subplots(figsize=(10, 6))
    for product_code, sales_by_date in product_sales_by_date.items():
        sales_for_product = []
        for date in all_dates_full:
            quantity = sales_by_date[date]
            sales_for_product.append(quantity)
            ax.scatter(date, quantity, color= '#0ADD08')  # Display quantity sold as dots
            ax.annotate(quantity, (date, quantity), textcoords="offset points", xytext=(0,10), ha='center')  # Annotate the dot with quantity sold
        ax.plot(all_dates_full, sales_for_product, linestyle='-', label=f'Product {product_code}')

    ax.set_xlabel('Date')
    ax.set_ylabel('Quantity Sold')
    ax.set_title('Product Sales Over Time')
    ax.legend()
    ax.grid(True)
    plt.xticks(rotation=45)

    # Save the line chart visualization as bytes in memory
    buf_line_chart = io.BytesIO()
    plt.savefig(buf_line_chart, format='png')
    plt.close()  # Close the figure to free memory
    buf_line_chart.seek(0)

    return buf_line_chart

# Define a command handler for the /reports command
async def reports(update: Update, context: CallbackContext) -> None:
    """Fetch and display reports."""
    try:
        # Fetch report data from the API endpoint
        response = requests.get(f"{API_ENDPOINT}/reports/")
        response.raise_for_status()  # Raise an error for non-2xx status codes

        # Parse the JSON response
        report_data = response.json()

        # Process and visualize the report data
        if report_data:
            # Generate the bar chart visualization
            buf_bar = generate_bar_chart(report_data)
            # Send the bar chart visualization to the user with a caption
            # await update.message.reply_photo(buf_bar, caption="Bar Chart: Stock In vs Stock Out")

            # Fetch sales transaction data from the API endpoint
            sales_response = requests.get(f"{API_ENDPOINT}/sales-transactions/")
            sales_response.raise_for_status()  # Raise an error for non-2xx status codes

            # Parse the JSON response for sales transactions
            sales_data = sales_response.json()

            # Process and visualize the sales transaction data
            if sales_data:
                # Generate the sales bar chart visualization
                # buf_sales_chart = generate_sales_bar_chart(sales_data)
                
                # Send the sales bar chart visualization to the user with a caption
                # await update.message.reply_photo(buf_sales_chart, caption="Total Sales Quantity for Each Product")
                

                # Generate the line chart visualization for product sales over time
                buf_line_chart = generate_sales_time_series_chart(sales_data)
                # Send the line chart visualization to the user with a caption
                # await update.message.reply_photo(buf_line_chart, caption="Product Sales Over Time")

                    # Generate the top ten products bar chart visualization
                buf_top_ten_products_bar_chart = generate_top_ten_products_bar_chart(sales_data)
                # Send the top ten products bar chart visualization to the user with a caption
                # await update.message.reply_photo(buf_top_ten_products_bar_chart, caption="Bar Chart: Top Ten Products by Sales Quantity")
                
                # Send Grouped charts as an album with a singl caption
                images = [InputMediaPhoto(media=buf_line_chart), InputMediaPhoto(media=buf_top_ten_products_bar_chart)]
                caption = "Sales Reports (Total Sales Quantity for Each Product, Product Sales Over Time, Top Ten Products by Sales Quantity)"
                
                await update.message.reply_media_group(media=images, caption=caption)
                
            
            else:
                await update.message.reply_text("No sales transaction data available.")            

            # Fetch stock data from the API endpoint
            stock_response = requests.get(f"{API_ENDPOINT}/stocks/")
            stock_response.raise_for_status()  # Raise an error for non-2xx status codes
            
            # Parse the JSON response for stock data
            stock_data = stock_response.json()

            # Process and visualize the stock data
            if stock_data:
                # Generate the bar chart visualizations for stock products
                charts = generate_stock_bar_charts(API_ENDPOINT)
                if charts:
                    # Open each bar chart image and append it to a list
                    images = [InputMediaPhoto(media=chart) for chart in charts]
                    images.append(InputMediaPhoto(media=buf_bar))
                    # Send the images as an album with a single caption
                    caption = "Total Stock Transactions by Product (Stock In, Stock Out, Stock On Hand)"
                    await update.message.reply_media_group(media=images, caption=caption)
                else:
                    await update.message.reply_text("No stock data available.")
            else:
                await update.message.reply_text("No stock data available.")
             
            # Display the report data to the user
            best_selling_product = report_data.get('best_selling_product', {})
            least_selling_product = report_data.get('least_selling_product', {})
            
            report_txt = f"*Total Stock In :* _{report_data['total_stock_in']}_ 🟢\n" \
                        f"*Total Stock Out :* _{report_data['total_stock_out']}_ 🔺\n" \
                        f"*Total Stock On Hand :* _{report_data['total_stock_on_hand']}_ 🏪\n" \
                        f"*Total Stock Value :* _{report_data['total_stock_value']}_\n" \
                        f"*Best Selling Product :* {best_selling_product.get('products', 'N/A')} \n_Total Sold:_ (*{best_selling_product.get('quantity_sold', 'N/A')}*)\n" \
                        f"*Least Selling Product :* {least_selling_product.get('products', 'N/A')} \n_Total Sold:_ (*{least_selling_product.get('quantity_sold', 'N/A')}*)"     
            
            await update.message.reply_text(
                report_txt, parse_mode=ParseMode.MARKDOWN
            )

        else:
            await update.message.reply_text("No report data available.")

    except Exception as e:
        logger.error(f"Error fetching or displaying reports: {e}")
        await update.message.reply_text("An error occurred while fetching or displaying reports. Please try again later.")

async def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        f"Hello 👋 {update.message.from_user.username} You can interact with this bot by sending the following commands:\n\n"
        "/start - Start the bot\n"
        "/help - Get help on how to use the bot\n"
        "/products - View all products\n"
        "Add a Product (Button)- Add a new product to the inventory\n"
        "Record a Sale (Button) - Record a sale transaction\n"
        "Manage Stock (Button) - Update stock quantities\n"
        "Generate Reports (Button) - Generate sales and stock reports\n"
        
    )
    await update.message.reply_text(help_text)

async def cancel(update: Update, context: CallbackContext) -> int:
    """End and cancel the conversation."""
    await update.message.reply_text(
        "The conversation has been cancelled. Send /start to start a new conversation."
    )
    return ConversationHandler.END

def main():
    """Start the bot."""
    # Create the application and pass the bot token to it
    application = Application.builder().token(BOT_TOKEN).build()
    # Create a conversation handler for adding a product
    add_product_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r"^Add a Product$") & ~filters.COMMAND, start_add_product)],
        states={
            ADD_PRODUCT_NAME: [MessageHandler(filters.TEXT, add_product_name)],
            ADD_PRODUCT_CODE: [MessageHandler(filters.TEXT, add_product_code)],
            ADD_PRODUCT_DESCRIPTION: [MessageHandler(filters.TEXT, add_product_description)],
            ADD_PRODUCT_PRICE_1: [MessageHandler(filters.TEXT, add_product_price_1)],
            ADD_PRODUCT_PRICE_2: [MessageHandler(filters.TEXT, add_product_price_2)],
            ADD_PRODUCT_QUANTITY: [MessageHandler(filters.TEXT, add_product_quantity)],
            ADD_PRODUCT_IMAGE: [MessageHandler(filters.TEXT, add_product_image)],
            ADD_PRODUCT_CATEGORY: [CallbackQueryHandler(add_product_category)],
            ADD_PRODUCT_BRAND: [CallbackQueryHandler(add_product_brand)],
            ADD_PRODUCT_SIZE: [CallbackQueryHandler(add_product_size)],
            ADD_PRODUCT_COLOR: [CallbackQueryHandler(add_product_color)],  
        },
        fallbacks=[CommandHandler("cancel", cancel_add_product)],
    )
    
    # Create a conversation handler for sale
    sale_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex(r"^Record a Sale$") & ~filters.COMMAND, start_sale)],
    states={
        SALE_CATEGORY: [CallbackQueryHandler(select_sale_category)],
        SALE_PRODUCT_SELECTION: [CallbackQueryHandler(select_sale_product)],
        SALE_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_sale_quantity)],
        SALE_CONFIRMATION: [CallbackQueryHandler(finalize_sale)],
    },
    fallbacks=[CommandHandler("cancel", cancel_sale)],
)

    # Create a conversation handler for managing stock    
    stock_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r"^Manage Stock$") & ~filters.COMMAND, start_stock_update)],
        states={
            STOCK_PRODUCT_SELECTION: [CallbackQueryHandler(select_stock_product)],
            STOCK_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_stock_quantity)],
            ADD_NEW_STOCK_PRODUCT_SELECTION: [CallbackQueryHandler(add_new_stock)],
            ADD_NEW_STOCK_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_new_stock_quantity)],
        },
        fallbacks=[CommandHandler('cancel', cancel_stock_update)],
        allow_reentry=True  # Allow re-entry of conversation handler
    )
    
    
    application.add_handler(CommandHandler("start", start))

    # Add conversation handler for creating store
    start_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^' + BUTTON_CREATE_STORE + '$'), create_store)],
        states={
            CREATE_STORE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_store_name)],
            CREATE_STORE_CONFIRM: [MessageHandler(filters.Regex('^(Yes|No)$'), create_store_confirm)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    application.add_handler(start_conv_handler)
    # Add the conversation handlers to the application
    application.add_handler(add_product_handler)
    application.add_handler(sale_handler)
    
    
    # Add command handler for /stock_report
    # application.add_handler(CommandHandler("stock_report", stock_report))
    application.add_handler(stock_handler)
    
    application.add_handler(CommandHandler("products", start_slider))
    application.add_handler(CallbackQueryHandler(navigate_slider, pattern='^(prev|next)$'))
    
    application.add_handler(CommandHandler("reports", reports))
    application.add_handler(MessageHandler(filters.Regex(r"^Generate Reports$") & ~filters.COMMAND, reports))
    # Add the /start command handler to the application
    application.add_handler(CommandHandler("start", start))
    # Add the /help command handler to the application
    application.add_handler(CommandHandler("help", help_command))
    
    
    # Start the application
    application.run_polling()
    
if __name__ == "__main__":
    main()
    