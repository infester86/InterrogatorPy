import socket, threading, csv, binascii
from datetime import datetime
from time import sleep

# Variabeln
thres = 5000

# UDP Verbindung
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Erstelle ein UDP-Socket
sock.bind(('192.168.0.2', 8001)) # Binden Sie das Socket an eine Adresse und einen Port
server_address = ('192.168.0.19', 4567) 

# Empfangen von Daten 1x pro Sekunde
def receive_data():
    print('Daten werden ausgeweret')
    while True:
        data, _ = sock.recvfrom(4096)
        hex_data = binascii.hexlify(data).decode('utf-8')  # Umwandlung in eine Zeichenkette
        #print(hex_data)
        analyze_data(hex_data)
        sleep(1)    
    print("Daten werden nicht mehr ausgewertet")

# Send Befehle
def send_data(message): # So werden alle Befehle verschickt
    try:
        # Sende Daten
        #print('Sende {!r}'.format(message))
        sock.sendto(bytes.fromhex(message), server_address)
    except Exception as e:
        print('Fehler beim Senden von Daten: ', str(e))


def send_init(): 
    send_modulv()
    send_modulp()  # Modulparamater erfragen
    send_sweep()
    send_stop()

def send_modulv(): # Modulversion
    send_data('1001040000000000')

def send_modulp(): # Modulparameter
    send_data('1004040000000000')

def send_stop(): # Stop
    send_data('3001060000000000')

def send_readsn(): # Seriennummer auslesen
    send_data('1003040000000000')

def send_sweep():
    send_data('20010C0000000213EC000A0000000000')

def send_autogain_all(): # Autogainsettings
    send_data('2003060000000000')

def send_thres_all(thres):
    hex_number = format(thres, 'x')
    for i in range(8):
        send_data("2002060" + str(i) + hex_number)

def send_startreading(): # Mit dem auslesen der daten beginnen
    send_data('300206006500')
   
def send_readch(): # Platzhalter
    #send_data("300706000000")
    #send_data("300706000001")
    #send_data("300706000002")
    #send_data("300706000003")
    #send_data("300706000004")
    #send_data("300706000005")
    #send_data("300706000006")
    #send_data("300706000007")
    return

def read_sn(data):
    if data.startswith("10030008"):
        sn = data.split("10030008")
        print("SN: " + str(int(sn[1], 16)))
        return 
    
def read_modulepara(data):
    if data.startswith("1004000c"):
        print("Kanäle: " + str(int(data[12:16], 16)))
        print("FBGs: " + str(int(data[16:20], 16)))
        print("Peaks Intervall: " + str(int(data[20:24], 16)))

def read_moduleversion(data):
    if data.startswith("10010008"):
        print("Modulversion: " + str(int(data[12:16], 16)/100))

def read_chan(data): # Auslesen der ADC Daten Nicht fertig
    if data.startswith("3007000008040003"):
        print("Daten Channel 3")
        print("Gain: " + str(int(data[16:20], 16)))
        start_position = 20
        for i in range(2551):
            end_position = start_position + 4
            adc_data = int(data[start_position:end_position+1], 16)
            print(f"ADC Data {i+1}: {adc_data}")
            start_position = end_position

def read_fbgfrequency(data):
    if data.startswith("3002000003d6"):
        split_data = data.split("3002000003d6")
        messdaten = split_data[1]
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        sinvolledaten = [timestamp]
        split_messdaten = [messdaten[i:i+244] for i in range(0, len(messdaten), 244)]
        for i, d in enumerate(split_messdaten):
                #print(f"Teil {i+1}: {d}")
                komplett = d
                chandata = analyze_fbgfrequency_chan(komplett)
                if chandata != False:
                    sinvolledaten.append(chandata)
        save_wavelength(sinvolledaten)

# Berechnungsfunktionen
def calc_wavelength(daten):
    c = 3 * 10**8  # Lichtgeschwindigkeit in m/s
    daten_decimal = int(daten, 16)  # Umwandlung von Hexadezimal in Dezimal
    daten_decimal = daten_decimal / 10  # Umwandlung von GHz in Hz
    daten_decimal = daten_decimal * 10**9  # Umwandlung von GHz in Hz
    wellenlaenge = c / daten_decimal  # Berechnung der Wellenlänge
    return(wellenlaenge)

# Analysieren
def analyze_data(hexdata): # Alle Pakete die ausgewertet werden sollen
    read_sn(hexdata)
    read_modulepara(hexdata)
    read_moduleversion(hexdata)
    read_chan(hexdata)
    read_fbgfrequency(hexdata)


def analyze_fbgfrequency_chan(datenpaket): # Auswerten der FBG Frequenz Paket für jeweils einen Kanal
    n = 8
    kanaldaten = []
    split_strings = [datenpaket[i:i+n] for i in range(0, len(datenpaket), n)]
    for items in split_strings:
        daten = items[2:]   
        if len(daten) == 6:
            if daten != "000000":
                wellenlaenge = calc_wavelength(daten)      
                kanaldaten.append(wellenlaenge) 
        else:
            pass
    if len(kanaldaten) > 0:
        return(kanaldaten)
    else:
      return(False)


# Speichern
def save_wavelength(data):
    # Flattening der Liste
    flat_list = [data[0]] + [item for sublist in data[1:] for item in sublist]
    # Speichern der Daten in einer CSV-Datei
    with open('output.csv', 'a+', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(flat_list)





# Thread Starten
receive_thread = threading.Thread(target=receive_data, args=())
receive_thread.start()

# Befehle Senden
send_init()
send_readsn()
send_autogain_all()
send_sweep()
send_thres_all(thres)
sleep(5)                # Er braucht eine Pause
send_startreading()

