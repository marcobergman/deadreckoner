#!/usr/bin/env python
import wx
import socket
import time
import threading
import socket
import sys
import math
import time
import xml.etree.ElementTree as ET
import threading
from datetime import datetime
from random import random

TCP_LISTEN_PORT=20221
UDP_BROADCAST_PORT=10110


#TCP sending
#sendsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#server_address = ('localhost', 30330)
#sendsocket.connect(server_address)

#UDP ais broadcasting
sendsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sendsocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
print ("--- Broadcasting NMEA messges to UDP:"+str(UDP_BROADCAST_PORT))

#TCP nmea listener
listensocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listensocket.bind(("", TCP_LISTEN_PORT))
listensocket.listen(1)
print ("--- Listening to NMEA messages at TCP:" + str(TCP_LISTEN_PORT))



def nmeaChecksum(s): # str -> two hex digits in str
    chkSum = 0
    subStr = s[1:len(s)] # clip off the leading $ or !

    for e in range(len(subStr)):
        chkSum ^= ord((subStr[e]))

    hexstr = str(hex(chkSum))[2:4].upper()
    if len(hexstr) == 2:
        return hexstr
    else:
        return '0'+hexstr


def joinNMEAstrs(payloadstr): #str -> str
    tempstr = '!AIVDM,1,1,,A,' + payloadstr + ',0'
    result = tempstr + '*' + nmeaChecksum(tempstr) + "\r\n"
    return result


def num2bin (num, bitWidth):
    # deal with 2's complement
    # thx to https://stackoverflow.com/questions/12946116/twos-complement-binary-in-python
    num = int(num)
    num &= (2 << bitWidth-1)-1 # mask
    formatStr = '{:0'+str(bitWidth)+'b}'
    return formatStr.format(int(num))


def string2bin (myString, i_width):
    enc=''
    for i in range (len(myString)):
        enc += num2bin(ord(myString[i].upper()), 6)
        
    return enc.ljust(i_width, '0')[:i_width]



mapping = "0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVW`abcdefghijklmnopqrstuvw"
   
   
def ais_message1 (i_mtype, i_repeat, i_mmsi, i_status, i_turn, i_stw, i_accuracy, i_lat, i_lon, i_course, 
            i_hdg, i_second, i_maneuver, i_spare, i_raim, i_radio):
    bits = num2bin(i_mtype,6) + num2bin(i_repeat,2) + num2bin(i_mmsi, 30) + num2bin(i_status, 4) + \
        num2bin(int(4.733*math.sqrt(float(i_turn))), 8) + num2bin(i_stw*10, 10) + num2bin(i_accuracy, 1) + num2bin(int(600000*float(i_lon)), 28) + \
        num2bin(int(600000*float(i_lat)), 27) + num2bin(i_course*10, 12) + num2bin(i_hdg, 9) + num2bin(i_second, 6) + \
        num2bin(i_maneuver, 2) + num2bin(i_spare, 3) + num2bin(i_raim, 1) + num2bin(i_radio, 19)
    #print ("type..r.mmsi..........................sta.turn....stw.....alon.........................lat........................course......hdg..sec...m.sp.rradio..............")
    #print (bits)
    enc = ''
    while bits:
        n=int(bits[:6],2)
        enc = enc + mapping[n:n+1]
        bits = bits[6:]

    return '' + joinNMEAstrs(enc)
    

def ais_message5 (i_mtype, i_repeat, i_mmsi, i_version, i_imo, i_callsign, i_name, i_shiptype, i_to_bow, i_to_stern, i_to_port, i_to_stbd, 
            i_fixtype, i_eta_month, i_eta_day, i_eta_hour, i_eta_minute, i_draught, i_destination, i_dte, i_spare, i_filler):
    bits = num2bin(i_mtype, 6) + num2bin(i_repeat, 2) + num2bin(i_mmsi, 30) + num2bin(i_version, 2) + \
        num2bin(i_imo, 30) + string2bin(i_callsign, 42) + string2bin(i_name, 120) + num2bin(i_shiptype, 8) + \
        num2bin(i_to_bow, 9) + num2bin(i_to_stern, 9) + num2bin(i_to_port, 6) + num2bin(i_to_stbd, 6) + \
        num2bin(i_fixtype, 4) + num2bin(i_eta_month, 4) + num2bin(i_eta_day, 5) + num2bin(i_eta_hour, 5) + \
        num2bin(i_eta_minute, 6) + num2bin(i_draught, 8) + string2bin(i_destination, 120) + num2bin(i_dte, 1) + \
        num2bin(i_spare, 1) + num2bin(i_filler, 2)
    #print ("type..r.mmsi..........................v.imo...........................callsign..................................name..........................................................................................................stype...tobow....stern....port..stbd..fix.m...d....hour.min...draught.destination.............................................................................................................dsff")
    #print (bits)
    enc = ''
    while bits:
        n=int(bits[:6],2)
        enc = enc + mapping[n:n+1]
        bits = bits[6:]
        
    tempstr1 = '!AIVDM,2,1,3,A,' + enc[:59] + ',0'
    tempstr2 = '!AIVDM,2,2,3,A,' + enc[59:] + ',0'
    return  tempstr1 + '*' + nmeaChecksum(tempstr1) + "\r\n" + tempstr2 + '*' + nmeaChecksum(tempstr2) + "\r\n"
    # return '' + joinNMEAstrs(enc) 

    

def rmc_message(i_lat, i_lon, i_hdg, i_stw):
    t_ns = 'N' if i_lat > 0 else 'S'
    t_ew = 'E' if i_lon > 0 else 'W'
    i_lat = abs(i_lat)
    i_lon = abs(i_lon)
    t_lat = "%02.f%07.4f" % (math.trunc(i_lat), 60*(i_lat-math.trunc(i_lat)))
    t_lon = "%03.f%07.4f" % (math.trunc(i_lon), 60*(i_lon-math.trunc(i_lon)))
    t_time = datetime.utcnow().strftime("%H%M%S");
    t_date = datetime.utcnow().strftime("%d%m%y");

    tempstr = '$GPRMC,%s,A,%s,%s,%s,%s,%s,%s,%s,,' % (t_time, t_lat, t_ns, t_lon, t_ew, i_stw, i_hdg, t_date)
    result = tempstr + '*' + nmeaChecksum(tempstr) + "\r\n"
    return result

def gll_message(i_lat, i_lon, i_hdg, i_stw):
    t_ns = 'N' if i_lat > 0 else 'S'
    t_ew = 'E' if i_lon > 0 else 'W'
    i_lat = abs(i_lat)
    i_lon = abs(i_lon)
    t_lat = "%02.f%07.4f" % (math.trunc(i_lat), 60*(i_lat-math.trunc(i_lat)))
    t_lon = "%03.f%07.4f" % (math.trunc(i_lon), 60*(i_lon-math.trunc(i_lon)))
    t_date = datetime.utcnow().strftime("%d%m%y");
    t_time = datetime.utcnow().strftime("%H%M%S");

    tempstr = '$GPGLL,%s,%s,%s,%s,%s,A,C' % (t_lat, t_ns, t_lon, t_ew, t_time)
    result = tempstr + '*' + nmeaChecksum(tempstr) + "\r\n"
    return result

def mwv_message(i_awa, i_aws):
    t_awa = "%03.0f" % (float(i_awa))
    t_aws = "%03.1f" % (float(i_aws))
    tempstr = "$IIMWV,%s,R,%s,N,A" % (t_awa, t_aws)
    result = tempstr + '*' + nmeaChecksum(tempstr) + "\r\n"
    return result

def vhw_message(i_hdm, i_stwn):
    t_hdm = "%03.0f" % (float(i_hdm))
    t_stwn = "%03.1f" % (float(i_stwn))
    tempstr = "$IIVHW,,,%s,M,%s,N,," % (t_hdm, t_stwn)
    result = tempstr + '*' + nmeaChecksum(tempstr) + "\r\n"
    return result


def hdm_message(i_hdm):
    t_hdm = "%03.1f" % (float(i_hdm))
    
    tempstr = "$KKHDM,%s,M" % (t_hdm)
    result = tempstr + '*' + nmeaChecksum(tempstr) + "\r\n"
    return result


def dbk_message(i_dbk):
    t_dbk = "%03.1f" % (float(i_dbk))
    
    tempstr = "$INDBK,,f,%s,M,,F" % (t_dbk)
    result = tempstr + '*' + nmeaChecksum(tempstr) + "\r\n"
    return result


class Simulation(object):
    def __init__(self):
        # self.drlat = 0;
        # self.drlon = 0;
        
        self.gpslat = 0;
        self.gpslon = 0;
        self.gps_ts = 0;
        
        self.stw = 0;
        self.stw_count = 0;
        self.stw_sum = 0;
        self.stw_sum = 0;
        self.hdg = 0;
        self.hdg_count = 0;
        self.hdg_sum = 0;
        self.stwhdg_ts = 0;
        
        self.interval = 0;
        
        self.showAis = True;
        self.autoRead = True;

    def read_nmea_tcp_thread(self):
        while True:
            print ("Awaiting connection...")
            c,a = listensocket.accept()
            print ("Connection from: " + str(a) )
            while True:
                try:
                    m,x = c.recvfrom(1024)
                    if m:
                        first_line = m.decode().split("\r\n")[0]
                        line_elements = first_line.split(",")
                        if line_elements[0][3:] == "RMC":
                            self.gpslat = float(line_elements[3][0:2]) + float(line_elements[3][2:])/60
                            if line_elements[4] == "S":
                                self.gpslat = -self.gpslat
                            self.gpslon = float(line_elements[5][0:3]) + float(line_elements[5][3:])/60
                            if line_elements[6] == "W":
                                self.gpslon = -self.gpslon
                            self.gps_ts = time.time()
                            if self.autoRead:
                                drBoat.lat = self.gpslat
                                drBoat.lon = self.gpslon
                                drBoat.last_move = time.time()
                        if line_elements[0][3:] == "HDT":
                            self.hdg_sum += float(line_elements[1])
                            self.hdg_count += 1
                            self.hdg = self.hdg_sum / self.hdg_count
                            self.stwhdg_ts = time.time()
                        if line_elements[0][3:] == "VHW":
                            self.stw_sum += float(line_elements[5])
                            self.stw_count += 1
                            self.stw = self.stw_sum / self.stw_count
                            self.stwhdg_ts = time.time()
                    else:
                        break;
                except Exception as e:
                    print ("exception: " + str(e))
                    pass
            print ("Disconnected")
        print ("Ending thread")

        
    class Boat(object):
        def __init__(self, mmsi, name, lat, lon, hdg, stw, status, maneuver, own):
            self.mmsi = mmsi
            self.name = name
            self.lat = float(lat)
            self.lon = float(lon)
            self.stw = float(stw)
            self.hdg = float(hdg)
            self.status = status
            self.maneuver = maneuver
            self.own = own
            self.last_move = time.time()
            self.twd = 0
            self.tws = 0
            self.twv = 0
            self.curs = 0
            self.curd = 0


        def show(self):
            if self.own == False:
                my_message = \
                    ais_message1 (1, 0, self.mmsi, self.status, 0, self.stw, 1, self.lat, self.lon, 
                        self.hdg, self.hdg, 0, self.maneuver, 0, 0, 0) + \
                    ais_message5 (i_mtype=5, i_repeat=1, i_mmsi=self.mmsi, i_version=0, i_imo=0, i_callsign="PB0000", i_name=self.name, \
                        i_shiptype=79, i_to_bow=100, i_to_stern=50, i_to_port=15, i_to_stbd=15, i_fixtype=3, i_eta_month=0, i_eta_day=0, \
                        i_eta_hour=24, i_eta_minute=60, i_draught=50, i_destination="Timbuktu", i_dte=1, i_spare=0, i_filler=0)
            else:
                # calculate apparent wind:
                #print ("self.stw = %3f  self.tws=%3f  self.twd=%3f  self.hdg=%3f" % (self.stw, self.tws, self.twd, self.hdg))
                twa = (((self.twd + random() * 10 - self.hdg + 180) %360) - 180)/180*math.pi
                aws = math.sqrt(self.stw**2+self.tws**2 + 2 * self.stw*self.tws*math.cos(twa))
                try:
                    angle = math.acos((self.tws * math.cos(twa) + self.stw)/(math.sqrt(self.tws**2 + self.stw**2 + 2*self.tws*self.stw*math.cos(twa))))/math.pi*180
                except:
                    angle = 0
                if (twa < 0):
                    angle = -(angle)
                #print ("angle=" + str(angle))
                awa = (angle) % 360 
                depth = 4-(math.sin(time.time()/20)+1)**2;
                my_message = rmc_message (self.lat, self.lon, self.hdg, self.stw) + \
                                gll_message(self.lat, self.lon, self.hdg, self.stw) + \
                                mwv_message(awa, aws) + \
                                hdm_message(self.hdg) + \
                                vhw_message(self.hdg, self.stw) + \
                                dbk_message(depth)
            #sys.stdout.write (my_message)    

            # TCP
            #sendsocket.sendall((my_message+"\r\n").encode('utf-8'))

            # UDP
            sendsocket.sendto((my_message).encode('utf-8'), ('<broadcast>', UDP_BROADCAST_PORT))
            
        def move(self, speedup):
            elapsed = time.time() - self.last_move
            self.lat = self.lat + elapsed * self.stw/3600/60 * speedup * math.cos(self.hdg/180*math.pi)
            self.lon = self.lon + elapsed * self.stw/3600/60 * speedup * math.sin(self.hdg/180*math.pi) / math.cos(self.lat/180*math.pi)
            
            # apply current
            self.lat = self.lat + elapsed * self.curs/3600/60 * speedup * math.cos(self.curd/180*math.pi)
            self.lon = self.lon + elapsed * self.curs/3600/60 * speedup * math.sin(self.curd/180*math.pi) / math.cos(self.lat/180*math.pi)

            self.last_move = time.time()


    def moveDrBoat(self):
        print ('move')
        drBoat.move(1);
        if self.showAis:
            drBoat.show();
            
        self.hdg_sum = 0
        self.hdg_count = 0
        self.stw_sum = 0
        self.stw_count = 0
        
        return


    def loadBoat(self):

        global drBoat 
        drBoat = self.Boat("000000000", "Estimated Position", float(52.9), float(4.42), float(0), float(0), 1, 0, False)
                        
        return True


        
    def processBoats(self):
        drBoat.move()
        self.timer = threading.Timer(1, self.processBoats)
        self.timer.start()
    


    def startBoat(self, event):
        self.loadBoats()

        try:
            self.timer.cancel()
        except:
            pass
        print ("--- Starting simulation")
        self.timer = threading.Timer(1, self.processBoats)
        self.timer.start()
        self.paused = False

        

    def stopBoats(self, event):
        try:
            self.timer.cancel()
            print ("--- Stopping simulation, stop sending NMEA messages")
        except:
            pass

            

    def wrapup(self):
        print ("--- Closing UDP socket")
        sendsocket.close()
        #listensocket.close()
        
        

simulation = Simulation()

global read_nmea_tcp_thread
read_nmea_tcp_thread = threading.Thread(target = simulation.read_nmea_tcp_thread, daemon=True)
read_nmea_tcp_thread.start()

class SimulatorFrame(wx.Frame):

    def __init__(self, parent, title):
        super(SimulatorFrame, self).__init__(parent, title = title, size=(490,200))

        self.InitUI()
        self.Centre()
        self.Show()

    def InitUI(self):

        panel = wx.Panel(self)
        sizer = wx.GridBagSizer(0,0)

        ## Set up Statictext
        
        text14 = wx.StaticText(panel)
        sizer.Add(text14, pos = (0, 5), flag = wx.ALL, border = 3)
        
        global drBoat
        ## Setup up controls
        text1 = wx.StaticText(panel, label = "GPS")
        sizer.Add(text1, pos = (0, 0), flag = wx.ALL, border = 3)
        
        text2 = wx.StaticText(panel, label = "LAT")
        sizer.Add(text2, pos = (0, 1), flag = wx.ALL, border = 3)
        textGpsLat = wx.TextCtrl(panel, value="", size=(70,20))
        sizer.Add(textGpsLat, pos = (0, 2), flag = wx.EXPAND|wx.ALL, border = 3)
        textGpsLat.Disable()

        text3 = wx.StaticText(panel, label = "LON")
        sizer.Add(text3, pos = (0, 3), flag = wx.ALL, border = 3)
        textGpsLon = wx.TextCtrl(panel, value="", size=(70,20))
        sizer.Add(textGpsLon, pos = (0, 4), flag = wx.EXPAND|wx.ALL, border = 3)
        textGpsLon.Disable()

        text4 = wx.StaticText(panel, label = "DR")
        sizer.Add(text4, pos = (1, 0), flag = wx.ALL, border = 3)
        
        text5 = wx.StaticText(panel, label = "LAT")
        sizer.Add(text5, pos = (1, 1), flag = wx.ALL, border = 3)
        textDrLat = wx.TextCtrl(panel, value="", size=(70,20))
        sizer.Add(textDrLat, pos = (1, 2), flag = wx.EXPAND|wx.ALL, border = 3)
        def OnChange_drlat(event):
            drBoat.lat = float(textDrLat.GetValue())
        textDrLat.Bind(wx.EVT_TEXT, OnChange_drlat, textDrLat)

        text6 = wx.StaticText(panel, label = "LON")
        sizer.Add(text6, pos = (1, 3), flag = wx.ALL, border = 3)
        textDrLon = wx.TextCtrl(panel, value="", size=(70,20))
        sizer.Add(textDrLon, pos = (1, 4), flag = wx.EXPAND|wx.ALL, border = 3)
        def OnChange_drlon(event):
            drBoat.lon = float(textDrLon.GetValue())
        textDrLon.Bind(wx.EVT_TEXT, OnChange_drlon, textDrLon)

        text7 = wx.StaticText(panel, label = "Boat")
        sizer.Add(text7, pos = (2, 0), flag = wx.ALL, border = 3)
        text8 = wx.StaticText(panel, label = "HDG")
        sizer.Add(text8, pos = (2, 1), flag = wx.ALL, border = 3)
        textHdg = wx.TextCtrl(panel, value="0", size=(70,20))
        sizer.Add(textHdg, pos = (2, 2), flag = wx.EXPAND|wx.ALL, border = 3)
        def OnChange_Hdg(event):
            drBoat.hdg = float(textHdg.GetValue())
        textHdg.Bind(wx.EVT_TEXT, OnChange_Hdg, textHdg)

        text9 = wx.StaticText(panel, label = "STW")
        sizer.Add(text9, pos = (2, 3), flag = wx.ALL, border = 3)
        textStw = wx.TextCtrl(panel, value="0", size=(70,20))
        sizer.Add(textStw, pos = (2, 4), flag = wx.EXPAND|wx.ALL, border = 3)
        def OnChange_Stw(event):
            drBoat.stw = float(textStw.GetValue())
        textStw.Bind(wx.EVT_TEXT, OnChange_Stw, textStw)

        text10 = wx.StaticText(panel, label = "Current")
        sizer.Add(text10, pos = (3, 0), flag = wx.ALL, border = 3)
        text11 = wx.StaticText(panel, label = "DIR")
        sizer.Add(text11, pos = (3, 1), flag = wx.ALL, border = 3)
        textCurDir = wx.TextCtrl(panel, value="0", size=(70,20))
        sizer.Add(textCurDir, pos = (3, 2), flag = wx.EXPAND|wx.ALL, border = 3)
        def OnChange_CurDir(event):
            drBoat.curd = float(textCurDir.GetValue())
        textCurDir.Bind(wx.EVT_TEXT, OnChange_CurDir, textCurDir)

        text12 = wx.StaticText(panel, label = "Speed")
        sizer.Add(text12, pos = (3, 3), flag = wx.ALL, border = 3)
        textCurSpd = wx.TextCtrl(panel, value="0", size=(70,20))
        sizer.Add(textCurSpd, pos = (3, 4), flag = wx.EXPAND|wx.ALL, border = 3)
        def OnChange_CurSpd(event):
            drBoat.curs = float(textCurSpd.GetValue())
        textCurSpd.Bind(wx.EVT_TEXT, OnChange_CurSpd, textCurSpd)

        text13 = wx.StaticText(panel, label = "DR Interval (s)")
        sizer.Add(text13, pos = (4, 1), flag = wx.ALL, border = 3)
        textInterval = wx.TextCtrl(panel, value="10", size=(70,20))
        sizer.Add(textInterval, pos = (4, 2), flag = wx.EXPAND|wx.ALL, border = 3)
        def OnChange_Interval(event):
            drBoat.interval = float(textInterval.GetValue())
        textInterval.Bind(wx.EVT_TEXT, OnChange_Interval, textInterval)

        # Checkboxes
        def onAutoReadToggle(event):
            simulation.autoRead = event.IsChecked()
        checkAutoRead = wx.CheckBox(panel, label="DR follows GPS")
        checkAutoRead.SetValue(True)
        sizer.Add(checkAutoRead, pos = (1, 5), flag = wx.ALIGN_LEFT|wx.ALL, border = 3)
        checkAutoRead.Bind(wx.EVT_CHECKBOX, onAutoReadToggle)
        
        def onAutoDrToggle(event):
            if event.IsChecked():
                self.drTimer.Start(int(textInterval.GetValue())*1000)
            else:   
                self.drTimer.Stop()
        checkAutoDr = wx.CheckBox(panel, label="DR Automatic")
        sizer.Add(checkAutoDr, pos = (4, 5), flag = wx.ALIGN_LEFT|wx.ALL, border = 3)
        checkAutoDr.Bind(wx.EVT_CHECKBOX, onAutoDrToggle)
        checkAutoDr.SetValue(True)
        
        def onShowAisToggle(event):
            simulation.showAis = event.IsChecked()
        checkShowAis = wx.CheckBox(panel, label="Show AIS")
        checkShowAis.SetValue(True)
        sizer.Add(checkShowAis, pos = (5, 5), flag = wx.ALIGN_LEFT|wx.ALL, border = 3)
        checkShowAis.Bind(wx.EVT_CHECKBOX, onShowAisToggle)
        
        # Set up buttons
        def onMoveDrBoat(event):
            simulation.moveDrBoat()
            if checkAutoDr.GetValue():
                self.drTimer.Start(int(textInterval.GetValue())*1000)
        buttonDrNow = wx.Button(panel, label = "DR Now" )
        sizer.Add(buttonDrNow, pos = (4, 4), flag = wx.ALIGN_CENTER|wx.ALL, border = 3)
        buttonDrNow.Bind(wx.EVT_BUTTON, onMoveDrBoat);

        def updateScreen(self):
            elapsed = ""         
            if (simulation.gps_ts != 0) :
                elapsed = "   " + str(int(time.time() - simulation.gps_ts)) +"s"
            text14.SetLabel (elapsed)
            
            if (int(time.time() - simulation.gps_ts) <= 10) :
                textGpsLat.SetValue(str(simulation.gpslat))
                textGpsLon.SetValue(str(simulation.gpslon))
            
            if (int(time.time() - simulation.stwhdg_ts) <= 10) :
                textHdg.SetValue(str(simulation.hdg))
                textStw.SetValue(str(simulation.stw))
                textHdg.Disable()
                textStw.Disable()
            else:
                textHdg.Enable()
                textStw.Enable()
                
            textDrLat.SetValue(str(drBoat.lat))
            textDrLon.SetValue(str(drBoat.lon))
                
            if checkAutoRead.GetValue() or checkAutoDr.GetValue():
                textDrLat.Disable()
                textDrLon.Disable()
            else:
                textDrLat.Enable()
                textDrLon.Enable()
            
        
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, updateScreen, self.timer)
        self.timer.Start(1000)
        
        self.drTimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, onMoveDrBoat, self.drTimer)
        
        panel.SetSizerAndFit(sizer)

        self.Bind(wx.EVT_CLOSE, self.OnExitApp)

        self.drTimer.Start(int(textInterval.GetValue())*1000)
                
    def OnExitApp(self, event):
        print ('--- Window closed')
        simulation.stopBoats(event)
        simulation.wrapup()
        self.Destroy()

simulation.loadBoat()

app = wx.App()
myFrame = SimulatorFrame(None, title = 'Dead Reckoner')
app.MainLoop()

