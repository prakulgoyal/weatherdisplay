import sys
import os
import logging
import time
import smbus
from PIL import Image, ImageDraw, ImageFont

# --- 1. Tell Python where your Waveshare driver is ---
sys.path.append('/home/prakul/epaper/e-Paper/RaspberryPi_JetsonNano/python/lib')
from waveshare_epd import epd2in9_V2

# --- 2. Logging and Hardware Config ---
logging.basicConfig(level=logging.INFO)

bus = smbus.SMBus(1)
DEVICE_ADDRESS = 0x77

# --- 3. BMP180 Raw Math ---
def read_bmp180():
    try:
        cal = bus.read_i2c_block_data(DEVICE_ADDRESS, 0xAA, 22)
        
        def get_short(index):
            val = (cal[index] << 8) + cal[index+1]
            return val - 65536 if val > 32767 else val

        def get_ushort(index):
            return (cal[index] << 8) + cal[index+1]

        # Calibration coefficients
        AC1, AC2, AC3 = get_short(0), get_short(2), get_short(4)
        AC4, AC5, AC6 = get_ushort(6), get_ushort(8), get_ushort(10)
        B1, B2 = get_short(12), get_short(14)
        MB, MC, MD = get_short(16), get_short(18), get_short(20)

        # Read raw temperature
        bus.write_byte_data(DEVICE_ADDRESS, 0xF4, 0x2E)
        time.sleep(0.005)
        msb, lsb = bus.read_i2c_block_data(DEVICE_ADDRESS, 0xF6, 2)
        UT = (msb << 8) + lsb

        # True Temperature calculations
        X1 = ((UT - AC6) * AC5) / 32768.0
        X2 = (MC * 2048.0) / (X1 + MD)
        B5 = X1 + X2
        temp = (B5 + 8.0) / 160.0

        return temp
    except Exception as e:
        logging.error(f"I2C Bus Error: {e}")
        return None

# --- 4. Single Execution ---
try:
    temperature = read_bmp180()
    
    if temperature is not None:
        logging.info(f"Read Temperature: {temperature:.2f} °C")
        
        logging.info("Initializing e-Paper Display...")
        epd = epd2in9_V2.EPD()
        epd.init()
        epd.Clear(0xFF)

        # Dimensions for landscape mode
        width = epd.height  # 296
        height = epd.width  # 128

        # Create fresh image canvas
        image = Image.new('1', (width, height), 255)
        draw = ImageDraw.Draw(image)
        
        # Load fonts (using standard Raspberry Pi system fonts)
        try:
            font_large = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 65)
            font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
        except IOError:
            # Fallback if system fonts aren't accessible
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Prepare the text strings
        temp_text = f"{temperature:.1f}°C"
        time_text = f"{time.strftime('%H:%M')}"

        # Calculate text dimensions for precise placement
        temp_bbox = draw.textbbox((0, 0), temp_text, font=font_large)
        temp_w = temp_bbox[2] - temp_bbox[0]
        temp_h = temp_bbox[3] - temp_bbox[1]

        time_bbox = draw.textbbox((0, 0), time_text, font=font_small)
        time_w = time_bbox[2] - time_bbox[0]
        time_h = time_bbox[3] - time_bbox[1]

        # Calculate X, Y coordinates for Centered Temp / Bottom Right Time
        temp_x = (width - temp_w) // 2
        temp_y = (height - temp_h) // 2 - 10  # Shift slightly up for visual balance
        
        time_x = width - time_w - 5           # 5px padding from right edge
        time_y = height - time_h - 5          # 5px padding from bottom edge

        # Draw the text to the canvas
        draw.text((temp_x, temp_y), temp_text, font=font_large, fill=0)
        draw.text((time_x, time_y), time_text, font=font_small, fill=0)

        # Rotate canvas for proper landscape layout mapping
        final_image = image.rotate(90, expand=True)
        epd.display(epd.getbuffer(final_image))

        logging.info("Putting display into low-power sleep mode...")
        epd.sleep()
        logging.info("Success!")
        
    else:
        logging.error("Failed to fetch sensor data.")

except Exception as e:
    logging.error(f"Execution Error: {e}")
