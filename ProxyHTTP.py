import socket
import threading
import signal
import sys
import sys, errno



config =  {
            "HOST_NAME" : "127.0.0.1",
            "BIND_PORT" : 12345,
            "MAX_REQUEST_LEN" : 1024,
            "CONNECTION_TIMEOUT" : 5
          }

def HTTP_request_he_to_she(http_request):
    lines = http_request.split('\n')
    index = False
    text = ""
    for i in range(len(lines)) :
        if lines[i] == "" :
            try :
                index = i+1
                text = lines[i+1]
            except IndexError :
                return False

        if "Content-Type: image" in lines[i] :
            return False

    text.replace(" he ", " she ")
    print(text)
    if index != False :
        lines[index] = text
    else :
        return False
    return lines




class Server:

    def __init__(self, config):
        signal.signal(signal.SIGINT, self.shutdown) 
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)     # Cree une socket TCP
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serverSocket.bind((config['HOST_NAME'], config['BIND_PORT'])) # Associe la socket au serveur proxy
        self.serverSocket.listen(10)
        self.__clients = {}



    def listenForClient(self):
        while True:
            (clientSocket, client_address) = self.serverSocket.accept() 
            d = threading.Thread(name=self._getClientName(client_address), target=self.proxy_thread, args=(clientSocket, client_address))
            d.setDaemon(True)
            d.start()
        self.shutdown(0,0)


    def proxy_thread(self, conn, client_addr):
        request_from_browser = conn.recv(config['MAX_REQUEST_LEN'])  #Recup le requête
        request_from_proxy = request_from_browser

        first_line = request_from_browser.split(b'\n')[0] 
        try :                 
            url = first_line.split(b' ')[1]   
        except IndexError :
            url = "" 
        print("URL : ")
        print((url[:50]))
        http_pos = url.find(b"://") 
        if (http_pos==-1):
            temp = url
        else:
            temp = url[(http_pos+3):] 

        port_pos = temp.find(b":")

        webserver_pos = temp.find(b"/")
        if webserver_pos == -1:
            webserver_pos = len(temp)

        webserver = ""
        port = -1
        if (port_pos==-1 or webserver_pos < port_pos): 
            port = 80
            webserver = temp[:webserver_pos]
        else:                                       
            port = int((temp[(port_pos+1):])[:webserver_pos-port_pos-1])
            webserver = temp[:port_pos]

        try:
            # Cree une socket pour se connecter au serveur web
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(config['CONNECTION_TIMEOUT'])
            s.connect((webserver, port))
            s.sendall(request_from_proxy)                          

            while 1:
                data_from_server = s.recv(config['MAX_REQUEST_LEN']) 
                data_from_proxy = data_from_server

                if (len(data_from_proxy) > 0):
                    conn.send(data_from_proxy) 
                else:
                    break
            s.close()
            conn.close()
        except socket.error as error_msg:
            print(('ERROR: ',client_addr,error_msg))
            if s:
                s.close()
            if conn:
                conn.close()


    def _getClientName(self, cli_addr):

        return "Client"


    def shutdown(self, signum, frame):
        self.serverSocket.close()
        sys.exit(0)


if __name__ == "__main__":
    server = Server(config)
    server.listenForClient()
