# -*- coding: utf-8 -*-
"""
Modified: Jan 22, 2020

@author: g.gurkan
ver 3 Update: Serial is replaced by Bluetooth Lib.
# revision, 7 Jun 2020: Filter data, rather than calculated slope vector!
# revision, 7 Jun 2020: Import both filtered and raw slope vector!
"""


from PyQt4.QtCore import *
from PyQt4.QtGui import *
import gui_motion_ver2
import sys
import numpy as np
from numpy.linalg import norm
import pyqtgraph
from bluetooth import *
import time
import glob
import configSensors as cs
import scipy.signal as sp

class Kafes(QMainWindow,gui_motion_ver2.Ui_MainWindow):
    x_curves=['','','','','']
    y_curves=['','','','','']
    z_curves=['','','','','']   
    colors=['b','r','g','y','m']
    
    
    samples = 0
    DEVICE_ADDRESS = '98:D3:32:70:B8:16'
    PLOT_BUFFER = np.zeros((200,6),int)
    
    
    
    def __init__(self,parent=None):
        global RECORDING, CONNECTED, params
        RECORDING, CONNECTED = False, False
        
        super(Kafes,self).__init__(parent)
        self.setupUi(self)
        
        params = cs.devDual()
        self.buttonConnect.clicked.connect(self.handleCon)
        self.buttonRec.clicked.connect(self.handleRec)
        self.buttonOpenfile.clicked.connect(self.openFile)
        self.buttonApplyFilter.clicked.connect(self.applyFilter)
        self.buttonSetFilename.clicked.connect(self.setFileName)
        self.accplotx.plotItem.sigRangeChanged.connect(self.syncAnalysisLimits)
        self.buttonExport.clicked.connect(self.exportData)
        
        self.preparePlot(self.accplotx,"X-axis","Acceleration",'g')
        self.preparePlot(self.accploty,"Y-axis","Acceleration",'g')
        self.preparePlot(self.accplotz,"Z-axis","Acceleration",'g')
        self.preparePlot(self.angleplot,"Estimated Angle","Angle",'deg')

        self.buttonApplyFilter.setEnabled(False)
        self.groupFilter.setEnabled(False)
        self.rootdir = glob.os.getcwd()
        
        #Led Colors
        
        self.LedOFF =QPixmap(10,10)
        self.LedOFF.fill(Qt.red)
        
        self.LedON =QPixmap(10,10)
        self.LedON.fill(Qt.green)
        self.ledConnection.setPixmap(self.LedOFF)
        self.ledRecording.setPixmap(self.LedOFF)
        
   
    def preparePlot(self,item,title,ylabel,yunits):
        item.setLabel('left',ylabel, units=yunits)
        item.setBackground(background=QColor(240,240,240))
        item.setLabel('bottom',"Time",units='s')
        item.showGrid(x=True, y=True, alpha=0.5)
        item.setTitle(title)
        

    def handleCon(self):
        global RECORDING, CONNECTED, acquisition, file_name
     
        self.groupFilter.setEnabled(False)
        if not(CONNECTED):
            self.statusbar.showMessage("Establishing connection...")
            acquisition = threadSerial(self.DEVICE_ADDRESS,self)
            acquisition.finished.connect(self.onFinished)
            acquisition.sig_StatusMessage.connect(self.statusbar.showMessage)
            if CONNECTED:
                self.statusbar.showMessage("Connected...")
                self.buttonConnect.setEnabled(True)
                self.groupRec.setEnabled(True)
                self.buttonRec.setEnabled(True)
                self.buttonOpenfile.setEnabled(False)
                self.buttonConnect.setText("Disconnect")
                self.lineEdit_Filename.setText(self.defaultFilename())
                self.setFileName()
                self.ledConnection.setPixmap(self.LedON)
                acquisition.start()
            else:
                QMessageBox.critical(None,"Connection Error","Connection Failed!...")
                self.buttonConnect.setEnabled(True)
                self.statusbar.showMessage("No device connected...")
                self.ledConnection.setPixmap(self.LedOFF)
        else:#Close Connection
            CONNECTED = False
            acquisition.terminate()
            while not(acquisition.terminated):
                print "Waiting..."
                continue
            
            self.buttonConnect.setText("Connect")
            self.groupRec.setEnabled(False)
            self.buttonOpenfile.setEnabled(True)
            self.ledConnection.setPixmap(self.LedOFF)
            
            
    
    def setFileName(self):
        global file_name
        file_name = self.lineEdit_Filename.text() + ".log"
        

    def handleRec(self):
        global RECORDING, CONNECTED, file_obj, file_name
        
        self.groupFilter.setEnabled(False)
        if not(RECORDING):
            
                file_obj = open(file_name,'w')
                RECORDING=True
                self.buttonRec.setText("Stop Recording")
                self.buttonConnect.setEnabled(False)
                self.buttonSetFilename.setEnabled(False)
                self.ledRecording.setPixmap(self.LedON)
                self.clearRawPlots()
        else:
            RECORDING=False
            time.sleep(.5)
            file_obj.close()
            while not(file_obj.closed):
                continue
            self.buttonRec.setText("Start Recording")
            self.buttonConnect.setEnabled(True)
            self.buttonConnect.setEnabled(True)
            self.buttonSetFilename.setEnabled(True)
            self.ledRecording.setPixmap(self.LedOFF)
            
                
    def defaultFilename(self):
        return time.strftime("REC-%Y%m%d-%H%M%S")
    
    def defaultExpFilename(self):
        return time.strftime("FILTERED-%Y%m%d-%H%M%S")

    def onFinished(self):
        global sub, acquisition, RECORDING, file_obj, CONNECTED
        
        if CONNECTED:
            N=len(sub)
            self.PLOT_BUFFER=np.row_stack((self.PLOT_BUFFER,sub))
            self.PLOT_BUFFER=np.delete(self.PLOT_BUFFER,np.arange(N),axis=0)
            self.plotData(self.PLOT_BUFFER)
            if RECORDING:
                np.savetxt(file_obj,sub[1:,:],fmt='%d',delimiter=",")
            acquisition.start()
        else:
            self.statusbar.showMessage('Disconnected...')
            self.clearAnglePlot()
            self.clearRawPlots()

    def onStatusUpdate(self,message):
        self.statusbar.showMessage(message)

    def openFile(self):
        self.file2Open = QFileDialog.getOpenFileNameAndFilter(None, 'Select a log file:', self.rootdir)
        
        if self.file2Open[0] !='':
            try:
                self.filedata = np.loadtxt(str(self.file2Open[0]),dtype='int',delimiter=',',skiprows=0)
                self.plotData(self.filedata)
                self.groupFilter.setEnabled(True)
                self.buttonExport.setEnabled(False)
                
            except ValueError:
                QMessageBox.critical(None,"Open File Error...","File can not be opened!...")
                self.filedata=[]
                self.groupFilter.setEnabled(False)
 
    def syncAnalysisLimits(self):
        [rangex, rangey] = self.sender().vb.viewRange()
        if True: #self.syncAnalysisCheck_X.isChecked():
            self.accploty.plotItem.vb.setRange(xRange=rangex,padding=0)
            self.accplotz.plotItem.vb.setRange(xRange=rangex,padding=0)
            
        if False: #self.syncAnalysisCheck_Y.isChecked():
            self.accploty.plotItem.vb.setRange(yRange=rangey)
            self.accplotz.plotItem.vb.setRange(yRange=rangey)

    def plotData(self,data):
        global params
      
        self.AnalysisSamples = len(data)
        self.tlabel = np.arange(0,len(data)/200.,1/200.)
        data_corrected = params.gain*(data.T-params.offset)
        self.AnalysisData = data_corrected.T.copy()
        self.govde =self.AnalysisData[:,:3].copy()
        self.kafa = self.AnalysisData[:,3:].copy()
        #self.slopes=map(lambda x,y: -np.rad2deg(np.arcsin(norm(np.cross(x,y))/(norm(x)*norm(y)))),self.govde,self.kafa)
        self.slopes=map(lambda x,y: np.rad2deg(np.arcsin(norm(np.cross(x,y))/(norm(x)*norm(y))))*np.sign(np.cross(x,y)[0,0]),self.govde,self.kafa)
        
        self.clearAnglePlot()
        self.angleplot.plot(self.tlabel,self.slopes,pen='b')
        self.buttonApplyFilter.setEnabled(True)

        if not(RECORDING):
            self.xRange= (0,self.AnalysisSamples/200.)
            self.yRangeAng=(np.min(self.slopes)-10,np.max(self.slopes)+10)
            self.angleplot.plotItem.vb.setRange(xRange=self.xRange,yRange=self.yRangeAng)
            
            self.clearRawPlots()
            self.AnalysisXcurves = []
            self.AnalysisYcurves = []
            self.AnalysisZcurves = []
            names= ['Torso','Head']
            self.accplotx.addLegend(size=(3,15),offset=(-5,5))
            self.accplotx.plotItem.vb.setRange(xRange=self.xRange)
            for c in range(2):
                self.AnalysisXcurves.append(self.accplotx.plot(pen=self.colors[c],width=3,name=names[c]))
                self.AnalysisYcurves.append(self.accploty.plot(pen=self.colors[c]))
                self.AnalysisZcurves.append(self.accplotz.plot(pen=self.colors[c]))
                
                self.AnalysisXcurves[c].setData(self.tlabel,np.squeeze(np.asarray(self.AnalysisData[:,3*c])))
                self.AnalysisYcurves[c].setData(self.tlabel,np.squeeze(np.asarray(self.AnalysisData[:,3*c+1])))
                self.AnalysisZcurves[c].setData(self.tlabel,np.squeeze(np.asarray(self.AnalysisData[:,3*c+2])))
        
            
    def clearRawPlots(self):
        self.accplotx.clear()
        self.accploty.clear()
        self.accplotz.clear()
        
    def clearAnglePlot(self):
        self.angleplot.clear()
    
    def applyFilter(self):
        
        global Forder, Fcutoff,Ftype, Fdata
        
        Fcutoff = int(self.paramCutoff.text())
        Forder = int(self.paramOrder.text())
        cutoffN = 2*int(Fcutoff)/200.
        
        if (Forder % 2)==0:
            Forder+=1
            self.paramOrder.setText(str(Forder))
        
        if self.comboFilterType.currentIndex()==0:
            Ftype ='LP'
            #self.tabs = sp.firwin(Forder,cutoffN)
            self.tabs_b,self.tabs_a = sp.butter(Forder,cutoffN)
        elif self.comboFilterType.currentIndex()==1:
            Ftype ='HP'
            #self.tabs = sp.firwin(Forder,cutoffN,pass_zero=False)
            self.tabs_b,self.tabs_a = sp.butter(Forder,cutoffN,btype='high')
        self.Data2Filter = np.matrix(sp.lfilter(self.tabs_b,self.tabs_a,self.AnalysisData.copy(),axis=0))
        self.govde2filter= self.Data2Filter[:,:3].copy()
        self.kafa2filter= self.Data2Filter[:,3:].copy()
        
        Fdata=map(lambda x,y: np.rad2deg(np.arcsin(norm(np.cross(x,y))/(norm(x)*norm(y))))*np.sign(np.cross(x,y)[0,0]),self.govde2filter,self.kafa2filter)
        #Fdata=map(lambda x,y:-np.rad2deg(np.arcsin(norm(np.cross(x,y))/(norm(x)*norm(y)))),self.govde2filter,self.kafa2filter)
        self.angleplot.clear()
        self.angleplot.plot(self.tlabel,self.slopes,pen='b')
        shift = (Forder-1)/2
        
        self.angleplot.plot(self.tlabel[:-shift],Fdata[shift:],pen='r')
        self.buttonExport.setEnabled(True)
        
    def exportData(self):
        global Forder, Fcutoff,Ftype, Fdata
        fname, retVal = QInputDialog.getText(self,'Export Data:',"Enter File Name:",QLineEdit.Normal,self.defaultExpFilename())
        if retVal:
            headerExp = 'Filter Type: Butterworth ' + Ftype + '\nCut-off Freq. = ' + str(Fcutoff) + '\nOrder: '+ str(Forder) 
            try:
                np.savetxt(fname+'.log',np.hstack((np.matrix(self.slopes).T,np.matrix(Fdata).T)),header=headerExp,fmt='%.3f')
                self.statusbar.showMessage('Export complete...')
            except:
                self.statusbar.showMessage('Export failed...' + sys.exc_info()[0])
    

class threadSerial(QThread):
    sig_StatusMessage  = pyqtSignal(str)
    
    def __init__(self,BTaddress, parent):
        super(threadSerial,self).__init__(parent)
        global CONNECTED, sub, RECORDING
        try:
            self.ser_obj = BluetoothSocket(RFCOMM)
            self.ser_obj.connect((BTaddress,1))
            time.sleep(1)
            self.res=""
            self.samples=0
            self.frame=1
            CONNECTED=True
            self.RUNNING = True
            time.sleep(.1)
            self.ser_obj.send('g')
            time.sleep(.1)
        except:
            CONNECTED = False
            

    def run(self):
        global CONNECTED, sub, RECORDING
        
        if CONNECTED:
            
            raw = self.ser_obj.recv(1000)
            time.sleep(.1)
            if self.frame==1:
                raw= raw[raw.find('\n')+1:]
            else:
                raw = self.res + raw
            clean_indx = raw[::-1].find('\n')
            if clean_indx>0:
                self.res = raw[-clean_indx:] # missing data segment to be put at the beginning of the next data segment
                raw = raw[:-clean_indx-1] # correct data segment
            else:
                self.res=""
            data =map(lambda x: np.fromstring(x,sep=',',dtype=np.int16),raw.split())
            ind = 0
            sub = np.zeros((0,6),dtype=np.int16)#!! 3-> 6
            for i in data:
                if len(i)<6:
                    print "Frame: %d, Index: %s, List:%s" % (self.frame,ind,i)
                sub = np.vstack((sub,i))
                ind +=1
            self.frame += 1
            #np.savetxt(file_obj,sub[1:,:],fmt='%d',delimiter=",")
            self.samples +=len(sub)
            if not(RECORDING):
                self.sig_StatusMessage.emit("Acquiring data...")
            else:
                self.sig_StatusMessage.emit("Saving...")
           

    def terminate(self):
        global CONNECTED, sub, RECORDING

        self.RUNNING=False
        
        self.sig_StatusMessage.emit("Disconnecting...")
        time.sleep(.5)        
        self.ser_obj.send('f')
        time.sleep(.5)        
        self.ser_obj.send('r')
        time.sleep(.5)
        self.ser_obj.close()
        time.sleep(.5)
        RECORDING = False
        CONNECTED = False
        
        
                
        
        
        
        
        
        
        
        
        
        
        
        
        
            
        
        
        
        

        



app=QApplication(sys.argv)
form=Kafes()
form.show()
app.exec_()