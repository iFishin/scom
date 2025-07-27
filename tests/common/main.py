import sys
import os

# Add the project root directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.common import force_decode




if __name__ == "__main__":
    # Example usage of force_decode
    byte_data = b'AT+QVERSION\r\n+QVERSION: HCM010SAAR01A02K07\r\n\r\nOK\r\nTEST\b1'
    decoded_data = force_decode(byte_data, handle_control_char='escape')
    print(decoded_data)  # Should print the escaped version of the byte data