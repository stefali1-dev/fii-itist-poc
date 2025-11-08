#!/usr/bin/env python3
import time
import serial
import boto3
import json
from PIL import Image, ImageEnhance


PORT = "/dev/rfcomm0"

# TODO: set these for your environment
QUEUE_URL = "https://sqs.eu-central-1.amazonaws.com/873550638583/fii-task-queue"
AWS_REGION = "eu-central-1"  # e.g. "eu-central-1"

from PIL import Image
MAX_LEN = 30


def send_image_to_printer(ser, image_path):
    """
    Convert an image to high-contrast black & white ESC/POS format
    and send it to the printer.

    - Resizes so max width/height = 384 px (keeps aspect ratio)
    - Transparent + white background ends up as "no print"
    """

    # 1. Open image, keep alpha to handle transparency
    img = Image.open(image_path).convert("RGBA")

    # 2. Resize so both width and height are <= 384, preserving aspect ratio
    max_size = 384
    w, h = img.size
    scale = min(max_size / w, max_size / h, 1.0)  # never upscale
    if scale < 1.0:
        new_w = int(w * scale)
        new_h = int(h * scale)
        img = img.resize((new_w, new_h))
    width, height = img.size

    # 3. Flatten transparency onto white background
    #    -> fully transparent areas become white (so they don't print)
    white_bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    img = Image.alpha_composite(white_bg, img)

    # 4. Convert to grayscale
    img = img.convert("L")

    # 5. Increase contrast (high contrast)
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.5)  # tweak factor if needed

    # 6. Apply a strong threshold: only dark pixels become black
    #    White / near-white background becomes pure white (no print)
    threshold = 200  # higher = less printed, more "background"
    img = img.point(lambda p: 0 if p < threshold else 255, "1")  # 1-bit B/W

    # ESC/POS command: bit image mode - GS v 0
    escpos_header = b"\x1d\x76\x30\x00"

    # Convert pixels to bytes
    bytes_per_row = (width + 7) // 8
    data = bytearray()

    for y in range(height):
        for x in range(0, width, 8):
            byte = 0
            for bit in range(8):
                if x + bit < width:
                    pixel = img.getpixel((x + bit, y))  # 0 (black) or 255 (white)
                    if pixel == 0:  # black pixel -> print dot
                        byte |= (1 << (7 - bit))
            data.append(byte)

    # Build full ESC/POS command
    width_low = bytes_per_row % 256
    width_high = bytes_per_row // 256
    height_low = height % 256
    height_high = height // 256

    cmd = bytearray()
    cmd += escpos_header
    cmd += bytes([width_low, width_high, height_low, height_high])
    cmd += data

    # Send to printer
    ser.write(cmd)
    ser.flush()

    # Feed a bit
    ser.write(b"\n" * 4)
    ser.flush()

    print(f"Printed image {image_path} ({width}x{height})")


def send_to_printer(ser, payload: dict):
    """
    Send a formatted ticket to the printer over the already-open serial connection.
    Expects a dict with keys: name, phone, ip.
    """
    name = payload.get("name", "N/A")
    phone = payload.get("phoneModel", "N/A")
    ip = payload.get("ip", "N/A")

    lines = [
        "", "", "", "", "",
        "Conferinta Fii-ITist 2025",
        "Hosts: ",
        "   Achitei Marius &",
        "   Stefan Leustean",
        "Presentation:",
        " Cloud Signal to Paper Trail:",
        " Python on AWS",
        "-" * 40,
        f"Name : {name}",
        f"Phone: {phone}",
        f"IP   : {ip}",
        "-" * 40,
        "Powered by",
        "  coffee, beer,"
        "  good vibes,",
        "  Python & AWS"
        "",
        "-" * 40,
        "", "", "", ""
    ]

    lines = [line[:MAX_LEN] for line in lines]

    text = "\r\n".join(lines) + "\r\n"

    # Encode as UTF-8 so emojis survive
    data = text.encode("utf-8")
    ser.write(data)
    ser.flush()
    print(f"Sent to printer:\n{text}")

def main():
    # Open serial connection once
    ser = serial.Serial(
        PORT,
        baudrate=9600,   # required by pyserial; BT ignores it but keep it set
        timeout=1,
    )

    # Create SQS client
    sqs = boto3.client("sqs", region_name=AWS_REGION)

    print("Starting SQS -> Bluetooth printer loop… (Ctrl+C to stop)")

    try:
        while True:
            # Long poll SQS for up to 20 seconds, 1 message at a time
            response = sqs.receive_message(
                QueueUrl=QUEUE_URL,
                MaxNumberOfMessages=1,   # process only one at a time
                WaitTimeSeconds=20,      # long polling
                VisibilityTimeout=60,    # give yourself time to print
            )

            messages = response.get("Messages", [])

            if not messages:
                # No message this poll -> wait 2 seconds and try again
                print("No messages, sleeping 2 seconds…")
                # time.sleep(2)
                continue

            # Process exactly one message
            msg = messages[0]
            body = msg["Body"]  # raw message body (string)
            
            body_dict = json.loads(body)
            
            formatted_body = json.dumps(body_dict, indent=2)

            print(f"Received message: {body!r}")

            # Here we just send the whole body to the printer.
            # You can parse JSON etc. if needed.
            ser = serial.Serial(PORT, baudrate=9600, timeout=1)
            # send_image_to_printer(ser, "logo.png")
            send_to_printer(ser, body_dict)

            # Delete the message so it won't be processed again
            sqs.delete_message(
                QueueUrl=QUEUE_URL,
                ReceiptHandle=msg["ReceiptHandle"],
            )
            print("Message deleted from SQS.")

            # Wait 2 seconds before polling again
            time.sleep(2)

    except KeyboardInterrupt:
        print("\nStopping loop due to KeyboardInterrupt.")
    finally:
        ser.close()
        print("Serial connection closed.")

if __name__ == "__main__":
    main()
