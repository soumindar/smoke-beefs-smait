//======================================
//================= Sapi ===============
#include "HX711.h"

const int LOADCELL_DOUT_PIN = 4;
const int LOADCELL_SCK_PIN = 5;
HX711 scale(4, 5);
float BERAT = 0;
float BERAT1 = 0;
float BERAT2 = 0;
float BERAT3 = 0;
float BERAT4 = 0;

int kalibrasi = 0;
byte limit1 = 48 ;
byte limit2 = 46 ;
byte limit3 = 44 ;
byte limit4 = 42 ;

byte val_limit1;
byte val_limit2;
byte val_limit3;
byte val_limit4;

byte in1 = 36 ;
byte in2 = 34 ;
byte in3 = 32 ;
byte in4 = 30 ;

byte IR1 = 2;
byte IR2 = 3;

byte val_IR1;
byte val_IR2;

int i=0;
int x=0;
char OK =0;

int KONTROL_IR = 26;



//==========================================
void setup()
{
  pinMode (KONTROL_IR,OUTPUT);
  pinMode (limit1,INPUT);
  pinMode (limit2,INPUT);
  pinMode (limit3,INPUT);
  pinMode (limit4,INPUT);

  pinMode (in1,OUTPUT);
  pinMode (in2,OUTPUT);
  pinMode (in3,OUTPUT);
  pinMode (in4,OUTPUT);

  digitalWrite (in1,LOW);
  digitalWrite (in2,LOW);
  digitalWrite (in3,LOW);
  digitalWrite (in4,LOW);
  
  pinMode (IR1,INPUT);
  pinMode (IR2,INPUT);

  Serial.begin(9600);
  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  scale.set_scale (-165851.f); //(2280.f);   // this value is obtained by calibrating the scale with known weights; see the README for details
  scale.tare();               // reset the scale to 0
  delay(1000);

}

//==========================================
void loop() 
{
  digitalWrite (KONTROL_IR, HIGH); // NYALAKAN IR
  STOP1();
  STOP2(); 
  //=============================================
  //------------ tutup pintu keluar -------------
  do{
    TUTUP2();
    //INFRARED();
    LIMIT();
  }while (val_limit4 !=0);
  STOP1();
  STOP2(); 
//================================================  
//=============== buka PINTU MASUK ================
  INFRARED();
  do{
    BUKA1();
    //INFRARED();
    LIMIT();
  }while (val_limit2 !=0);
  STOP1();
  STOP2(); 
  delay (1000);
  
  do{
    INFRARED();
  }while(val_IR1 != 0);
  delay(500);
  INFRARED();
  if ( val_IR1 == LOW)
  {
    do {
       INFRARED();
    }while (val_IR1 != 1);
  }
  delay(2000);
  //----------------- tutup pintu masuk ----------
  do{
    TUTUP1();
    //INFRARED();
    LIMIT();
   // Serial.println("tutup pintu masuk");
  }while (val_limit1 !=0);
  STOP1();
  STOP2(); 
//============================================
//=============== tutup pintu keluar ========
  do{
    TUTUP2();
    //INFRARED();
    LIMIT();
   // Serial.println("tutup pintu keluar");
  }while (val_limit4 !=0);
  STOP1();
  STOP2(); 
//============================================
  digitalWrite (KONTROL_IR, LOW); // MATIKA IR
//--------------------------------------------
//=========== timbang berat badan ============
 do
 {
  //===========================================
  //=========== timbang berat sapi ============
  long reading = scale.read();
  delay(50);
  BERAT = scale.get_units(6), 1;
  BERAT = BERAT*7.58;
  scale.power_down();              // put the ADC in sleep mode
  delay(10);
  scale.power_up();
  if (BERAT >= 0.2)
  {
    BERAT = scale.get_units(15), 1;
    BERAT = BERAT*7.58;
    if (x == 0)
    {
      BERAT1 = BERAT;
    }
    if (x == 1)
    {
      BERAT2 = BERAT;
      //Serial.print("BERAT2= ");
     // Serial.println(BERAT2);
     // Serial.println(" Kg");
    }
    if (x == 2)
    {
      BERAT3 = BERAT;
    }
    if (x == 3)
    {
      BERAT4 = BERAT;
     // x=0;
    }
    scale.power_down();              // put the ADC in sleep mode
    delay(20);
    scale.power_up();
    x++;
    /*
    Serial.print("BERAT1= ");
    Serial.print(BERAT1);
    Serial.println(" Kg");

    Serial.print("BERAT2= ");
    Serial.print(BERAT2);
    Serial.println(" Kg");

    Serial.print("BERAT3= ");
    Serial.print(BERAT3);
    Serial.println(" Kg");

    Serial.print("BERAT4= ");
    Serial.print(BERAT4);
    Serial.println(" Kg");
    */
  }
  
 }while( x != 4);
 STOP1();
 STOP2(); 
 x =0;
// Serial.print("VIX= ");
 Serial.println(BERAT4);
// Serial.println(" Kg");
 delay(10);

 //===============================
 //===== tunggu ada respons ======
  
  do 
  {
    if(Serial.available())
     {
       OK = Serial.read();
     }
  }while(OK != 'K');
  delay(1000);
  
  digitalWrite (KONTROL_IR, HIGH); // NYALAKAN IR
  OK = 0;
   
  //=============================
  delay(5000);
  //=============== buka PINTU KELUAR ================
  INFRARED();
  do{
    BUKA2();
    //INFRARED();
    LIMIT();
  }while (val_limit3 !=0);
  STOP1();
  STOP2(); 
  INFRARED();

   do{
    INFRARED();
  }while(val_IR2 != 0);
  delay(500);
  INFRARED();
  if ( val_IR2 == LOW)
  {
    do {
       INFRARED();
    }while (val_IR2 != 0);
  }
  delay(2000);
}

//=====================================
void INFRARED()
{
  val_IR1 = digitalRead( IR1);
  val_IR2 = digitalRead( IR2);
}

//======================================
void LIMIT()
{
  val_limit1 = digitalRead (limit1);
  val_limit2 = digitalRead (limit2);
  val_limit3 = digitalRead (limit3);
  val_limit4 = digitalRead (limit4);
}

//=======================================
void BUKA1()
{
  digitalWrite (in1,HIGH);
  digitalWrite (in2,LOW);
}
//=======================================
void BUKA2()
{
  digitalWrite (in3,HIGH);
  digitalWrite (in4,LOW);
}
//=======================================

void STOP1()
{
  digitalWrite (in1,LOW);
  digitalWrite (in2,LOW);
}
//=======================================
void STOP2()
{
  digitalWrite (in3,LOW);
  digitalWrite (in4,LOW);
}
//=======================================

void TUTUP1()
{
  digitalWrite (in1,LOW);
  digitalWrite (in2,HIGH);
}
//=======================================
void TUTUP2()
{
  digitalWrite (in3,LOW);
  digitalWrite (in4,HIGH);
}
//=======================================
