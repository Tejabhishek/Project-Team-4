#include <GSM.h>
	#include <LGSM.h>
	#include <LGPS.h>
	#include <Wire.h>
	#include <LTask.h>
	#include <LWiFi.h>
	#include <LWiFiClient.h>
	#include <LAudio.h>
	#include <LFlash.h>
	#include <LSD.h>
	#include <LStorage.h>
	#include <ADXL345.h>
	#include <stdlib.h>
	#include <Servo.h>
	#include <math.h>
	#include <avr/dtostrf.h>
	#include <string.h>
	//#include <HWSerial.h>
	

	#define Drv LFlash  
	

	char buff1[10];
	char buff2[10];
	

	// for GPS
	gpsSentenceInfoStruct info;
	char buff[256];
	 double latitude;
	 double longitude;
	 
	//for GSM
	char remoteNum[20]="+14088194712";
	#define PINNUMBER ""
	

	//for accelerometer
	ADXL345 accelerometer;
	

	//for wifi
	#define WIFI_AP "D-Link"
	#define WIFI_PASSWORD "Your Password here"
	#define WIFI_AUTH LWIFI_WPA // choose from LWIFI_OPEN, LWIFI_WPA, or LWIFI_WEP.
	#define SITE_URL "api.thingspeak.com"
	String api = "Write APIKEY here";
	LWiFiClient c;
	

	 
	GSM gsmAccess;
	GSM_SMS sms;
	

	void setup()
	{
	  pinMode(2,INPUT_PULLUP);
	  pinMode(3,OUTPUT);
	  digitalWrite(3,LOW);
	  Serial.begin(115200);
	  Drv.begin();
	   LGPS.powerOn();
	  Serial.println("LGPS Power on, and waiting ..."); 
	  
	   boolean notConnected = true;
	

	  // Start GSM shield
	  
	  while (notConnected)
	  {
	    if (gsmAccess.begin(PINNUMBER) == GSM_READY)
	      notConnected = false;
	    else
	    {
	      Serial.println("Not connected");
	      delay(1000);
	    }
	  }
	  
	  //accelerometer
	  if (!accelerometer.begin())
	  {
	    Serial.println("Could not find a valid ADXL345 sensor, check wiring!");
	    delay(500);
	  }
	  
	  // Values for Free Fall detection
	  accelerometer.setFreeFallThreshold(0.35); // Recommended 0.3 -0.6 g
	  accelerometer.setFreeFallDuration(0.1);  // Recommended 0.1 s
	

	  // Select INT 1 for get activities
	  accelerometer.useInterrupt(ADXL345_INT1);
	

	  // Check settings
	  checkSetup();\
	  
	  //For wifi
	  LWiFi.begin();
	

	  // keep retrying until connected to AP
	  Serial.println("Connecting to AP");
	  while (0 == LWiFi.connect(WIFI_AP, LWiFiLoginInfo(WIFI_AUTH, WIFI_PASSWORD)))
	  {
	    Serial.println(".");
	    delay(1000);
	  }
	  Serial.println("WiFi Connected");
	   
	  
	}
	

	void loop(void) 
	{
	  delay(50);
	  check();
	}
	void check()
	{
	

	  // Read values for activities
	  Vector norm = accelerometer.readNormalize();
	

	  // Read activities
	  Activites activ = accelerometer.readActivites();
	

	  if (activ.isFreeFall)
	  {
	    Serial.println("Free Fall Detected!");
	    LAudio.begin(); 
	    LAudio.playFile(storageFlash, (char*)"abc1.mp3");
	    Serial1.write("playing audio1"); 
	    LAudio.setVolume(5); 
	    sendmsg_and_upload();
	  }
	}
	

	

	

	

	

	void sendmsg_and_upload()
	{
	  int i = 0;
	  while(i<=50000)
	 {
	   if(digitalRead(2)==0)
	  {
	    check();
	  }
	  i++;
	}
	  //sending sms
	  Serial1.print("sending SMS");
	  char txtMsg[200]="met an accident... visit thingspeak to know the location";
	  sms.beginSMS(remoteNum);
	  sms.println(txtMsg);
	  sms.endSMS();
	  while(1)
	  {
	      //getting GPS data
	  LGPS.getData(&info);
	  Serial.println((char*)info.GPGGA); 
	  parseGPGGA((const char*)info.GPGGA);
	  //convert to string
	  dtostrf(latitude,9,6,buff1);
	  dtostrf(longitude,9,6,buff2);
	  //update
	  String string1,string2;
	  string1 = buff1;
	  string2 = buff2;
	  Update("field1="+string1+"&field2="+string2);
	  delay(30000);
	}
	}
	

	void Update(String data)
	{
	  if(c.connect(SITE_URL,80))
	  {
	    c.print("POST /update HTTP/1.1\n");
	c.print("Host: api.thingspeak.com\n");
	c.print("Connection: close\n");
	c.print("X-THINGSPEAKAPIKEY: "+api+"\n");
	c.print("Content-Type: application/x-www-form-urlencoded\n");
	c.print("Content-Length: ");
	c.print(data.length());
	c.print("\n\n");
	c.print(data);
	  
	  if (c.connected())
	{
	Serial.println("Uploaded to ThingSpeak...");
	Serial.println();
	}
	else
	{
	  Serial.println("failed to connect");
	}
	  }
	}
	

	void checkSetup()
	{
	  Serial.print("Free Fall Threshold = "); Serial.println(accelerometer.getFreeFallThreshold());
	  Serial.print("Free Fall Duration = "); Serial.println(accelerometer.getFreeFallDuration());
	}
	  
	

	static unsigned char getComma(unsigned char num,const char *str)
	{
	  unsigned char i,j = 0;
	  int len=strlen(str);
	  for(i = 0;i < len;i ++)
	  {
	     if(str[i] == ',')
	      j++;
	     if(j == num)
	      return i + 1; 
	  }
	  return 0; 
	}
	

	static double getDoubleNumber(const char *s)
	{
	  char buf[10];
	  unsigned char i;
	  double rev;
	  
	  i=getComma(1, s);
	  i = i - 1;
	  strncpy(buf, s, i);
	  buf[i] = 0;
	  rev=atof(buf);
	  return rev; 
	}
	

	static double getIntNumber(const char *s)
	{
	  char buf[10];
	  unsigned char i;
	  double rev;
	  
	  i=getComma(1, s);
	  i = i - 1;
	  strncpy(buf, s, i);
	  buf[i] = 0;
	  rev=atoi(buf);
	  return rev; 
	}
	

	void parseGPGGA(const char* GPGGAstr)
	{
	  /* Refer to http://www.gpsinformation.org/dale/nmea.htm#GGA
	   * Sample data: $GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47
	   * Where:
	   *  GGA          Global Positioning System Fix Data
	   *  123519       Fix taken at 12:35:19 UTC
	   *  4807.038,N   Latitude 48 deg 07.038' N
	   *  01131.000,E  Longitude 11 deg 31.000' E
	   *  1            Fix quality: 0 = invalid
	   *                            1 = GPS fix (SPS)
	   *                            2 = DGPS fix
	   *                            3 = PPS fix
	   *                            4 = Real Time Kinematic
	   *                            5 = Float RTK
	   *                            6 = estimated (dead reckoning) (2.3 feature)
	   *                            7 = Manual input mode
	   *                            8 = Simulation mode
	   *  08           Number of satellites being tracked
	   *  0.9          Horizontal dilution of position
	   *  545.4,M      Altitude, Meters, above mean sea level
	   *  46.9,M       Height of geoid (mean sea level) above WGS84
	   *                   ellipsoid
	   *  (empty field) time in seconds since last DGPS update
	   *  (empty field) DGPS station ID number
	   *  *47          the checksum data, always begins with *
	   */
	 
	  int tmp, hour, minute, second, num ;
	  if(GPGGAstr[0] == '$')
	  {
	    tmp = getComma(1, GPGGAstr);
	    hour     = (GPGGAstr[tmp + 0] - '0') * 10 + (GPGGAstr[tmp + 1] - '0');
	    minute   = (GPGGAstr[tmp + 2] - '0') * 10 + (GPGGAstr[tmp + 3] - '0');
	    second    = (GPGGAstr[tmp + 4] - '0') * 10 + (GPGGAstr[tmp + 5] - '0');
	    
	    sprintf(buff, "UTC timer %2d-%2d-%2d", hour, minute, second);
	    Serial.println(buff);
	    
	    tmp = getComma(2, GPGGAstr);
	    latitude = getDoubleNumber(&GPGGAstr[tmp]);
	    tmp = getComma(4, GPGGAstr);
	    longitude = getDoubleNumber(&GPGGAstr[tmp]);
	    sprintf(buff, "latitude = %10.4f, longitude = %10.4f", latitude, longitude);
	    Serial.println(buff); 
	    
	    tmp = getComma(7, GPGGAstr);
	    num = getIntNumber(&GPGGAstr[tmp]);    
	    sprintf(buff, "satellites number = %d", num);
	    Serial.println(buff); 
	  }
	  else
	  {
	    Serial.println("Not get data"); 
	  }
	}

