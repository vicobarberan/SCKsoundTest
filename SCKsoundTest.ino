#define S4                  A5          //MICRO
#define VCC                 3300.       //mV 
#define kr                  392.1568    //Constante de conversion a resistencia de potenciometrosen ohmios
#define RESOLUTION_ANALOG   4095.     //Resolucion de las entradas analogicas

#define POT1                 0x50    
#define POT2                 0x51    // Direction of the Potenciometer 2 for MICS heather voltage
#define POT3                 0x52    // Direction of the Potenciometer 3 for MICS measure
#define POT4                 0x53    // Direction of the Potenciometer 4 for sensor audio


//#define debugNOISE

//LED
#define RED     6
#define GREEN   12
#define BLUE    10

#include <Wire.h>
#include "Filter.h"


/*
High weights (90, for example) favor new data over old data. So, the output responds quickly to changes in the input and is not smoothed much.
Low values of (10, for example) favor old data over new data. So, the output is heavily smoothed and the filter responds slowly to changes (noisy or not) in the input.
Create a new exponential filter with a weight of 5 and an initial value of 0.
*/
ExponentialFilter<long> ADCFilter(30.0, 0.0);

int pause = 20;           // delay between loops
float timeElapsed = 0;

void setup() {
  Wire.begin(); 
  SerialUSB.begin(115200);

  while(!SerialUSB){
    }
  
  analogReadResolution(12);
  ledColor(0,0,255);
  
  float GAIN1 = 0;
  float GAIN2 = 400;
  writeGAIN(GAIN1,GAIN2);
  timeElapsed = millis();
}

void loop() {
  

  float RawValue = fastGetNoise();
  ADCFilter.Filter(RawValue);
 
  SerialUSB.print(ADCFilter.Current());         // 0 - Filtered Noise signal
  SerialUSB.print(",");
  SerialUSB.print(RawValue);                    // 1 - Raw Noise signal
  SerialUSB.print(",");
  SerialUSB.print(readGAIN());                  // 2 - Gain
  SerialUSB.print(",");
  SerialUSB.print(readResistor(6));             // 3 - Resistor 6
  SerialUSB.print(",");
  SerialUSB.print(readResistor(7));             // 4 - Resistor 7
  SerialUSB.print(",");
  SerialUSB.println((millis() - timeElapsed));    // 5 - Miliseconds since last output
  timeElapsed = millis();
  delay(pause);
  


  if (SerialUSB.available()) {
    byte buff = SerialUSB.read();
    String strBuff = "";
    strBuff = (char)buff;

    if (strBuff.equals("5")) {                  // 5 > resistor 6 UP
      writeResistor(6, readResistor(6)+kr+.1);
    } else if (strBuff.equals("4")) {           // 4 > resistor 6 Down
      writeResistor(6, readResistor(6)-kr);
    } else if (strBuff.equals("9")) {           // 9 > resistor 7 UP
      writeResistor(7, readResistor(7)+kr+.1);
    } else if (strBuff.equals("8")) {           // 8 > resistor 7 Down
      writeResistor(7, readResistor(7)-kr);
    } else if (strBuff.equals("1")) {           // 1 > Slower sampling
      pause = pause + 1;
    } else if (strBuff.equals("2")) {           // 2 > Faster sampling
      pause = pause - 1;
      if (pause < 5) pause = 5;
    }
  }

}

float fastGetNoise() {
  return (float)((analogRead(S4))/RESOLUTION_ANALOG)*VCC;
}

void NOISEini() {
    float GAIN1 = 0;
    float GAIN2 = 400;
    writeGAIN(GAIN1,GAIN2);
}
  
void writeGAIN(float GAIN1, float GAIN2) {
    writeResistor(6, GAIN1);
    delay(20);
    writeResistor(7, GAIN2);
}

float readGAIN() {
    return ((22000/(readResistor(6)+2440)+1)*(62000/readResistor(7)+1));
}   
 
float getNOISE() {  
    float GAIN1 = 0;
    float GAIN2 = 400;
    writeGAIN(GAIN1,GAIN2);
    float mVRaw = (float)((average(S4))/RESOLUTION_ANALOG)*VCC;
    
    #if debugNOISE
      SerialUSB.print("nOISE: ");
      SerialUSB.print(mVRaw);
      SerialUSB.print(" mV, RSpu: ");
      SerialUSB.print(readResistor(6));
      SerialUSB.print(", Ramp: ");
      SerialUSB.print(readResistor(7));
      SerialUSB.print(", GAIN: ");
      SerialUSB.println(readGAIN());
    #endif
    return mVRaw; 
}
  
float average(int anaPin) {
  int lecturas = 100;
  long total = 0;
  float average = 0;
  for(int i=0; i<lecturas; i++)
  {
    delay(1);
    total = total + analogRead(anaPin);
  }
  average = (float)total / lecturas;  
  return(average);
}

void writeResistor(byte resistor, float value) {
   
   if (value>100000) value = 0;
   else if (value<0) value = 100000;

   byte POT = POT1;
   byte ADDR = resistor;
   int data=0x00;
   
   data = (int)(value/kr);
   if ((resistor==6)||(resistor==7))
     {
       POT = POT4;
       ADDR = resistor - 6;
     }
   writeI2C(POT, ADDR, data);
}

void writeI2C(byte deviceaddress, byte address, byte data ) {
  Wire.beginTransmission(deviceaddress);
  Wire.write(address);
  Wire.write(data);
  Wire.endTransmission();
  delay(4);
}

float readResistor(byte resistor) {
   byte POT = POT1;
   byte ADDR = resistor;
   if ((resistor==2)||(resistor==3))
     {
       POT = POT2;
       ADDR = resistor - 2;
     }
   else if ((resistor==4)||(resistor==5))
     {
       POT = POT3;
       ADDR = resistor - 4;
     }
   else if ((resistor==6)||(resistor==7))
     {
       POT = POT4;
       ADDR = resistor - 6;
     }
   return readI2C(POT, ADDR)*kr;
}   

void ledColor(uint16_t red, uint16_t green, uint16_t blue){
  
  //up limit
  if (red > 255) red == 255;
  if (green > 255) green == 255;
  if (blue > 255) blue == 255;
  
  analogWrite(RED, abs(red - 255));
  analogWrite(GREEN, abs(green - 255));
  analogWrite(BLUE, abs(blue - 255));
}

byte readI2C(int deviceaddress, byte address ) {
  byte  data = 0x0000;
  Wire.beginTransmission(deviceaddress);
  Wire.write(address);
  Wire.endTransmission();
  Wire.requestFrom(deviceaddress,1);
  unsigned long time = millis();
  while (!Wire.available()) if ((millis() - time)>500) return 0x00;
  data = Wire.read(); 
  return data;
}  
