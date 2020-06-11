/*
 * Wireless Accelerometer System
 * Uses 1xHC-05 and 2xADXL345 accelerometers.
 * Accelerometer I2C addresses should be adjusted via SDO/ALT.ADDR pin.
 * Data Rate is 200 Hz.
 * 
 * HC-05 Bluetooth module should be connected to pins 7(RX->TX) and 8(TX->RX).
 * 
 * Author
 * Guray Gurkan
 * 
 * Date
 * 07 Jan 2018  
 */

#include <ADXL345dual.h>
#include <Wire.h>
#include <SoftwareSerial.h>


SoftwareSerial bt(7, 8); //RX,TX
unsigned long START;


bool BTmode;
bool go;
unsigned long tic;
int BTpin=12;

ADXL345 acc0, acc1;

char message[32];

void setup() {
  // put your setup code here, to run once:

  
  //Serial.begin(115200);
  pinMode(BTpin, OUTPUT);
  digitalWrite(BTpin,LOW);

  delay(3000);
  digitalWrite(BTpin,HIGH);
  delay(1000);
  bt.begin(115200);
  bt.setTimeout(.5);
  delay(1000);
  //bt.println("Waiting For Start (g)...");
  //Serial.println("Waiting For Start (g)...");
  do
  {
    delay(500);
  }
  while (bt.read() != 'g');
  //while (Serial.read() != 'g');
  //bt.println("Connection OK...");

  delay(10);
  acc0.begin(0);
  delay(1);
  acc1.begin(1);
  delay(1);
  acc0.setDataRate(0, ADXL345_DATARATE_200HZ);
  delay(1);
  acc1.setDataRate(1, ADXL345_DATARATE_200HZ);
  delay(1);
  acc0.setRange(0, ADXL345_RANGE_2G);
  delay(1);
  acc1.setRange(1, ADXL345_RANGE_2G);
  delay(1);
  //bt.println("Accelerometer OK");
  delay(1);
  //sendHeader("Dual Acc system",200,.0035);
  delay(1000);
  go = true;

  START = millis();

}

void loop() {

  if (bt.available() == 0 and go)
    //if (Serial.available() == 0 and go)
  {

 
    Vector raw = acc0.readRaw(0);
//     do
//    {
//    }
//    while (!acc0.readActivites(0).isDataReady);
//    
    Vector raw2 = acc1.readRaw(1);
    do
    {
    }
    while (!acc1.readActivites(1).isDataReady);

    /*


            Serial.print((int) raw.XAxis);
            Serial.print(",");
            Serial.print((int)raw.YAxis);
            Serial.print(",");
            Serial.println((int)raw.ZAxis);

    */

    //         BT Mode
    sprintf(message,"%d,%d,%d,%d,%d,%d\n",(int16_t)raw.XAxis,(int16_t)raw.YAxis,(int16_t)raw.ZAxis,(int16_t)raw2.XAxis,(int16_t)raw2.YAxis,(int16_t)raw2.ZAxis);
    bt.print(message);
//    bt.print((int16_t)raw.XAxis);
//    bt.print(",");
//    bt.print((int16_t)raw.YAxis);
//    bt.print(",");
//    bt.print((int16_t)raw.ZAxis);
//    bt.print(",");
//    bt.print((int) raw2.XAxis);
//    bt.print(",");
//    bt.print((int)raw2.YAxis);
//    bt.print(",");
//    bt.println((int)raw2.ZAxis);
    
    delayMicroseconds(10);

  }

  else if (bt.available())
  {
    byte val;
    val = bt.read();
    if (val == 'f')
    {
      //bt.println("");
      go = false;
    }
    else if (val=='r')
    {
      asm volatile ("  jmp 0");
    }
  }

  /*

    else if (Serial.available())
    {
      if (Serial.read() == 'f')
      {

        Serial.println(millis() - START);
        go = false;
      }
    }
  */
  delayMicroseconds(10);
}

void sendHeader(String device_name, int samplingfreq,  float LSB_per_g)
{
  bt.print("Log file of "); bt.println(device_name);
  bt.print("Sampling Frequency (Hz): ");bt.println(samplingfreq);
  bt.print("LSB per 1 g: ");bt.println(LSB_per_g);
  
  
  }
