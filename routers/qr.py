"""
Campus Café - QR Code Generator Router
---------------------------------------
This router dynamically generates a QR code image pointing to the public menu URL.
It automatically attempts to resolve the server's local area network (LAN) IP 
address so that external devices (like mobile phones) on the same Wi-Fi can 
scan and connect seamlessly, bypassing localhost loopbacks.

TODO:
    1. Support generating styled QR codes (e.g. customized colors, rounding, or embedding a café logo).
    2. Add PDF export feature for generating print-friendly flyers of the QR code.
"""

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import qrcode
import io
import socket

router = APIRouter(prefix="/api/qr", tags=["qr"])


def get_local_ip():
    """
    Attempts to discover the primary local area network (LAN) IP address of this computer.
    It does so by initiating a temporary UDP connection to a non-existent public IP,
    which triggers the system to resolve the outward-facing local interface IP.
    
    Falls back to '127.0.0.1' if no network connection is available.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # The address/port does not need to be reachable or run any service
        s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


@router.get("/menu")
def generate_qr(request: Request, base_url: str = None):
    """
    Generates a QR code image (PNG) pointing to the menu path.
    
    If 'base_url' is not provided in query parameters, it resolves it from the request.
    If the requesting host is identified as 'localhost' or '127.0.0.1', it resolves 
    and replaces the hostname with the LAN IP so that mobile scanners on the same Wi-Fi
    can access it.
    """
    if not base_url:
        port = request.url.port
        host = request.url.hostname
        
        # Override loopback hosts with the LAN IP address for QR code usability
        if host in ("localhost", "127.0.0.1"):
            host = get_local_ip()
            
        scheme = request.url.scheme
        if port:
            base_url = f"{scheme}://{host}:{port}"
        else:
            base_url = f"{scheme}://{host}"

    # Build QR target destination URL
    url = f"{base_url}/menu"
    
    # Configure QR code matrix properties
    qr = qrcode.QRCode(version=1, box_size=8, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    
    # Create the black and white image representation
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save the generated image binary bytes directly into an in-memory stream buffer
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    
    # Return the image bytes as a streaming response (avoids writing static files to disk)
    return StreamingResponse(buf, media_type="image/png")
