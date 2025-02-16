
from socket import *
s=socket(AF_INET, SOCK_DGRAM)
s.bind(('',10110))
while (1):
    m=s.recvfrom(1024)
    print (str(m[0],'utf-8'))
