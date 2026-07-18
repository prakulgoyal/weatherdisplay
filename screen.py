import sys
import os
import logging
from waveshare_epd import epd2in9_V2
from PIL import Image, ImageDraw, ImageFont

# Configure logging to see what's happening in the console
logging.basicConfig(level=logging.INFO)

try:
    logging.info("Initializing e-Paper...")
    epd = epd2in9_V2.EPD()
    epd.init()
    epd.Clear()

    # Dimensions for 2.9 inch V3: 
    # epd.height is 296, epd.width is 128
    width = epd.height   # 296
    height = epd.width   # 128
    
    logging.info(f"Creating canvas with size: {width}x{height}")
    # Create a blank white image
    image = Image.new('1', (width, height), 255)  
    draw = ImageDraw.Draw(image)

    # Use a default PIL font that is guaranteed to scale and render
    try:
        # This uses the default font bundled with PIL/Pillow
        font = ImageFont.load_default()
    except Exception:
        logging.warning("Could not load font, falling back to basic system font.")
        font = None

    logging.info("Drawing text and lines...")
    # Draw text (0 is Black, 255 is White)
    draw.text((10, 10), 'Hello World!', font=font, fill=0) 
    draw.line([(10, 30), (120, 30)], fill=0, width=2)

    # Rotate the image 90 degrees if the driver is strictly expecting vertical data mapping
    # (Often required for the V2/V3 display chip to correctly map a horizontal image)
    final_image = image.rotate(90, expand=True)

    logging.info("Sending image to display...")
    epd.display(epd.getbuffer(final_image))

    logging.info("Putting display to sleep...")
    epd.sleep()
    logging.info("Done!")

except IOError as e:
    logging.error(f"IOError: {e}")
    
except KeyboardInterrupt:    
    logging.info("ctrl + c:")
    epd2in9_V2.epdconfig.module_exit()
    exit()
