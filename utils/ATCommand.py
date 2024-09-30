from util_fish.common import *
import time

# Define the main port and baudrate
main_port = ""
baudrate = 115200
# main_uart_serial = None


def print_menu():
    menu_items = [
        ("q - Continue to execute command forcedly", "q"),
        ("w - Clean temp.txt", "w"),
        ("e - Clean ATCommand.txt", "e"),
        ("r - Clean temp.txt and run", "r"),
        ("t - Reset the Module & set echo on", "t"),
        ("y - Continue to receive the response", "y"),
        ("u - Update ATCommand.txt", "u"),
        ("i - Close the serial port", "i"),
        ("o - Open the serial port", "o"),
        ("p - Restore ATCommand.txt", "p"),
        ("x - Exit", "x")
    ]

    print("")
    print("-" * 23 + "Menu" + "-" * 23)
    for item, key in menu_items:
        print(f"{item:<40} - {key}")
        print("-" * 50)
    print("")

def execATCommand():

    uart_serial = None
    ATCommand = ""
    flag = False

    while True:
        
        print_menu()
        
        while True:
            if flag == True:
                print("🎉 ATCommand is `SAME` as last time, please select other options.")
            
            user_input = input("🎉 Enter your choice (q/w/e/r/t/y/u/i/o/p/x)(1|): ")
            if user_input == 'q' or user_input == 'Q':
                if uart_serial == None:
                    print("🎉 Please open the serial port first.")
                    main_port = port_select()
                    baudrate = baudrate_select()
                    uart_serial = port_on(main_port, baudrate)
                    flag = False
                    break
                else:
                    flag = False
                    break
            elif user_input == 'w' or user_input == 'W':
                with open(tmp_log, "w", encoding="utf-8") as file_object:
                    file_object.write("")
                print("🎉 Clean OK")
            elif user_input == 'e' or user_input == 'E':
                with open('./util_fish/ATCommand.txt', 'w', encoding='utf-8') as f:
                    f.write("")
                print("🎉 OK")
            elif user_input == 'r' or user_input == 'R':
                if uart_serial == None:
                    main_port = port_select()
                    baudrate = baudrate_select()
                    uart_serial = port_on(main_port, baudrate)
                reset(uart_serial)
                time.sleep(1)
                echo(uart_serial)

                with open(tmp_log, "w", encoding="utf-8") as file_object:
                    file_object.write("")
                # update ATCommand.txt
                update_AT_command()
                print("🎉 ATCommand.txt has been updated, modify the ATCommand and press `Enter` to continue...")
                keyboard.wait("enter")
                print("🎉 Start to execute AT command...")
                break
            elif user_input == 't' or user_input == 'T':
                reset(uart_serial)
                time.sleep(1)
                echo(uart_serial)
                print("🎉 Reset OK")
            elif user_input == 'y' or user_input == 'Y':
                start_time = time.time()
                while True:
                    response = port_read(uart_serial)
                    print_write(response)
                    if time.time() - start_time > 10:
                        break
            elif user_input == 'u' or user_input == 'U':
                update_AT_command()
                print("🎉 ATCommand.txt has been updated, modify the ATCommand and press `Enter` to continue...")
            elif user_input == 'i' or user_input == 'I':
                port_off(uart_serial)
                pass
            elif user_input == 'o' or user_input == 'O':
                main_port = port_select()
                baudrate = baudrate_select()
                uart_serial = port_on(main_port, baudrate)
                pass
            elif user_input == 'p' or user_input == 'P':
                restore_AT_command()
                print("🎉 ATCommand.txt has been restored.")
                pass


            elif user_input == '1':
                port_write('AT+QSTAAPINFO="fishpond","12345678"', uart_serial)
                while True:
                    response = port_read(uart_serial)
                    if '+QSTASTAT: "GOT_IP"' in response:
                        break
                print("🎉 WiFi connect OK!")
            elif user_input == 'x' or user_input == 'X':
                sys.exit()
            else:
                print("🎉 Invalid choice. Please try again.")
                
    
        with open ('./util_fish/ATCommand.txt', 'r', encoding='utf-8') as f:
            ATCommandFromFile = f.read().strip().split('\n')
        if ATCommand != ATCommandFromFile:
            ATCommand = ATCommandFromFile
            flag = False
   
        if flag == False:
            for item in ATCommand:
                if "`" in item:
                    continue
                elif "$" in item or "￥" in item:
                    item = item.replace("$", "").replace("￥", "")
                    port_write(item, uart_serial)
                    start_time = time.time()
                    while True:
                        response = port_read(uart_serial)
                        print_write(response)
                        if time.time() - start_time > 15:
                            break
                else:
                    port_write(item, uart_serial)
                    response = port_read(uart_serial)
                    print_write(response)
                    # if the command is the last one, wait for 3 seconds
                    if item == ATCommand[-1]:
                        start_time = time.time()
                        while True:
                            response = port_read(uart_serial)
                            print_write(response)
                            if time.time() - start_time > 5:
                                break
            flag = True
        else:
            pass
           
            


#####################################################################################################
#   
#   main entrance
#
#####################################################################################################
if __name__ == '__main__':
    
    
    logging.basicConfig(
    filename="error.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    # main_uart_serial = port_on(main_port, baudrate)

    # reset(main_uart_serial)
    # time.sleep(1)
    # echo(main_uart_serial)
    
    execATCommand()
    
    
    

