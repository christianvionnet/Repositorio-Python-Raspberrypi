import time
import RPi.GPIO as gpio
import mysql.connector
import serial
import os
import webbrowser

db = mysql.connector.connect(
    host="localhost",
    user="admin",
    passwd="sysadmin",
    database="Autoelevadores"
)

#Enable Serial Communication
port = serial.Serial("/dev/ttyAMA0", baudrate=9600, timeout=0.01)
counter=0
data=[]
Sentado = False
cursor = db.cursor()
resultado = 0
bandera = 0
mpo = 0
administrador = 0


LedVerde = 23
LedRojo = 18
Buzzer = 24
ReleElo = 25
ReleAuto = 22
Sensor = 27

#Designo las entradas y salidas
gpio.setmode(gpio.BCM)
gpio.setwarnings(False)
gpio.setup(LedRojo, gpio.OUT)
gpio.setup(LedVerde, gpio.OUT)
gpio.setup(Buzzer, gpio.OUT)
gpio.setup(ReleElo, gpio.OUT)
gpio.setup(ReleAuto, gpio.OUT)
gpio.setup(Sensor, gpio.IN) #sensor del asiento

#Seteo estado inicial apagado para los relés del monitor y del auto
#gpio.output(ReleElo, gpio.LOW)
gpio.output(ReleAuto, gpio.LOW)

def Cuenta(self):
    print("Se activó la interrupción")
    time.sleep(10)
    
    #Si sensor esta en bajo (usuario sentado) enciendo monitor y auto SÓLO si esta habilitado,
    #es decir tendría que volver a la funcion Lectura_Tarjeta
    if gpio.input(Sensor) == gpio.LOW :
        print("MANTENGO RELES encendidos")
        #gpio.output(ReleAuto, gpio.HIGH)
        #gpio.output(ReleElo, gpio.HIGH)
        #Lectura_Tarjeta(1)
        Sentado = True
        return
    else:
        gpio.output(ReleAuto, gpio.LOW)
        #gpio.output(ReleElo, gpio.LOW)
        print("RELES apagados")
        Sentado = False
        return

def Lectura_Tarjeta(self):
    #Defino las variables globales que usaré en esta función
    global resultado #Variable que uso para
    global Sentado #Variable para saber si el usuario está sentado o no / = True Sentado / = False No sentado
    global bandera #Bandera para usuario habilitado o no / = 1 SI / = 0 NO
    global mpo #Variable para
    
    time.sleep(1)
    print("Lectura de Tarjeta")
    print('Coloque su Tarjeta en el lector por favor')
    #Limpio el puerto serie antes de la lectura para evitar overreading
    port.flushInput()
    #Leo el puerto
    data = port.readline()
    while len(data) == 0:
        data = port.readline()
        print("Esperando lectura")
        
    dato = str(data)
    
    #Defino desde donde [8:] hasta donde [:8] me interesan los datos que recibo de la tarjeta
    tagID = dato[8:]
    tagID = tagID[:8]
    tagID = '0x00'+tagID
    tagIDd = int(tagID,16)
    #print(tagIDd)
    
    #Si recibo una lectura, tomo el id del usuario que se logueó para mostrar su nombre en pantalla 
    if len(data) > 0:
        cursor.execute("SELECT id, name FROM Usuarios WHERE rfid_uid = "+str(tagIDd))
        result = cursor.fetchone()
        
        
        if cursor.rowcount >= 1:
            print("Bienvenido " + result[1])
            #Inserto el nombre y la hora del usuario que se logueó
            cursor.execute("INSERT INTO ACCESOS (nombre) VALUES (%s)", (result[1],) )
            #Actualizo ese nombre en usuario activo para ver quien está usando el auto
            cursor.execute("UPDATE USUARIO_ACTIVO SET nombre = (%s)", (result[1],))
            #cursor.execute("INSTERT INTO USUARIO_ACTIVO (nombre) VALUES (%s)", (result[1],))
            #Enciendo led y buzzer
            gpio.output(LedVerde, gpio.HIGH) #Enciendo LED verde
            gpio.output(Buzzer, gpio.HIGH) #Enciendo BUZZER
            #gpio.output(ReleElo, gpio.HIGH) #Enciendo ReleElo
            time.sleep(1)
            gpio.output(LedVerde, gpio.LOW) #Apago LED verde
            gpio.output(Buzzer, gpio.LOW) #Apago BUZZER
            #gpio.output(ReleElo, gpio.LOW)
            db.commit()
            #Como es usuario habilitado, seteo bandera = 1
            bandera = 1

            #Selecciono los valores de los mpo de riesgo para saber que pantalla mostrar
            #despues de la de bienvenida con el nombre del usuario
            cursor.execute("SELECT mpo_1, mpo_2, mpo_3, mpo_7, mpo_8, mpo_9, mpo_10, habilitado FROM TABLA_MPO_1, TABLA_MPO_2, TABLA_MPO_3, HABILITACION ORDER BY TABLA_MPO_1.id DESC, TABLA_MPO_2.id DESC, TABLA_MPO_3.id DESC, HABILITACION.id DESC LIMIT 1")
            
            #Asigno esos valores a las variables mpo y enable
            result1 = cursor.fetchone()
            mpo1=result1[0]
            mpo2=result1[1]
            mpo3=result1[2]
            mpo7=result1[3]
            mpo8=result1[4]
            mpo9=result1[5]
            mpo10=result1[6]
            habilitado=result1[7]
            
            db.commit()
            
            #Selecciono los valores de los mpo de bajo riesgo para saber que pantalla mostrar
            #despues de la de bienvenida con el nombre del usuario
            cursor.execute("SELECT mpo_4, mpo_5, mpo_6, mpo_11, mpo_12 FROM TABLA_MPO_2, TABLA_MPO_3 ORDER BY TABLA_MPO_2.id DESC, TABLA_MPO_3.id DESC LIMIT 1")
            
            #Asigno esos valores a las variables mpo restantes
            result3 = cursor.fetchone()
            mpo4=result3[0]
            mpo5=result3[1]
            mpo6=result3[2]
            mpo11=result3[3]
            mpo12=result3[4]

            db.commit()
            
            cursor.execute("SELECT activo FROM NUEVO_TURNO")
            activo1 = cursor.fetchone()
            
            #Con los valores guardados, pregunto y verifico que pantalla mostrar
            #Uso banderaMpo como bandera para saber si MPO ok = 1 / MPO no ok = 0
            if activo1[0] == 1:
                webbrowser.open("http://localhost/bienvenido_nuevo_mpo.php",new=0)
            elif mpo1 == 0:
                webbrowser.open("http://localhost/bienvenido_riesgoalto.php",new=0)
                banderaMpo = 0
            elif mpo2 == 0:
                webbrowser.open("http://localhost/bienvenido_riesgoalto.php",new=0)
                banderaMpo = 0
            elif mpo3 == 0:
                webbrowser.open("http://localhost/bienvenido_riesgoalto.php",new=0)
                banderaMpo = 0
            elif mpo7 == 0:
                webbrowser.open("http://localhost/bienvenido_riesgoalto.php",new=0)
                banderaMpo = 0
            elif mpo8 == 0:
                webbrowser.open("http://localhost/bienvenido_riesgoalto.php",new=0)
                banderaMpo = 0
            elif mpo9 == 0:
                webbrowser.open("http://localhost/bienvenido_riesgoalto.php",new=0)
                banderaMpo = 0
            elif mpo10 == 0:
                webbrowser.open("http://localhost/bienvenido_riesgoalto.php",new=0)
                banderaMpo = 0
            elif mpo4 == 0:
                webbrowser.open("http://localhost/bienvenido_riesgobajo.php",new=0)
                banderaMpo = 1
            elif mpo5 == 0:
                webbrowser.open("http://localhost/bienvenido_riesgobajo.php",new=0)
                banderaMpo = 1
            elif mpo6 == 0:
                webbrowser.open("http://localhost/bienvenido_riesgobajo.php",new=0)
                banderaMpo = 1
            elif mpo11 == 0:
                webbrowser.open("http://localhost/bienvenido_riesgobajo.php",new=0)
                banderaMpo = 1
            elif mpo12 == 0:
                webbrowser.open("http://localhost/bienvenido_riesgobajo.php",new=0)
                banderaMpo = 1
            else:
                webbrowser.open("http://localhost/bienvenido_mpofinalizado.php",new=0)
                banderaMpo = 1
                
            time.sleep(2)

        #Si es usuario No valido, muestro mensaje, mantengo encendido monitor, pero apagado auto
        else:
            print("El usuario no existe/No esta habilitado.")
            gpio.output(LedRojo, gpio.HIGH)
            gpio.output(Buzzer, gpio.HIGH)
            time.sleep(0.1)
            gpio.output(LedRojo, gpio.LOW)
            gpio.output(Buzzer, gpio.LOW)
            time.sleep(0.1)
            gpio.output(LedRojo, gpio.HIGH)
            gpio.output(Buzzer, gpio.HIGH)
            time.sleep(0.1)
            gpio.output(LedRojo, gpio.LOW)
            gpio.output(Buzzer, gpio.LOW)
            time.sleep(0.1)
            gpio.output(LedRojo, gpio.HIGH)
            gpio.output(Buzzer, gpio.HIGH)
            time.sleep(0.1)
            gpio.output(LedRojo, gpio.LOW)
            gpio.output(Buzzer, gpio.LOW)
            #gpio.output(ReleElo, gpio.LOW)
            gpio.output(ReleAuto, gpio.LOW)
            bandera = 0
            #Muestro una pantalla de acceso denegado
            webbrowser.open("http://localhost/denegado.html",new=0)
            time.sleep(2)
            return
    #Limpio el puerto despues de la lectura para evitar overreading
    port.flushInput()
    
    #Consulto si estamos dentro de un turno nuevo para solicitar nuevo MPO
    cursor.execute("SELECT activo FROM NUEVO_TURNO")
    activo = cursor.fetchone()
    #Si activo = 0, el MPO ya se realizó en ese turno y no hace falta pedirlo de vuelta
    if activo[0] == 0:
        print("MPO ya realizado, se requerirá nuevamente en el próximo turno")
        #Consulto el estado del MPO solo para indicar si dió negativo o positivo
        if banderaMpo == 0:
            print("Dió negativo")
            gpio.output(ReleAuto, gpio.LOW)
        else:
            print("Dió positivo")
            gpio.output(ReleAuto, gpio.HIGH)

        time.sleep(2)
        
    #Si activo = 1, salto a este while. Mientras sea = 1 (hace falta hacer MPO), permanezco
    #dentro del bucle while, leyendo el valor de activo constantemente hasta que cambie a 0
    while activo[0] == 1 :
        time.sleep(1)
        db.commit()
        cursor.execute("SELECT activo FROM NUEVO_TURNO")
        activo = cursor.fetchone()
        print("Hace falta realizar el MPO en este turno")
        time.sleep(2)
        
        #Consulto si el MPO fue finalizado o si esta en curso
        cursor.execute("SELECT finalizado FROM FIN_DE_MPO")
        result0 = cursor.fetchone()
        print("finalizado vale: ")
        print(result0[0])
        #Mientras result0 = 0 (finalizado = 0) o sea que el MPO no se haya hecho todavia,
        #me quedo en el while esperando que se haga el mismo
        
        #Defino la variable i para el contador de espera para hacer MPO
        i = 0
        
        #Comienzo con el bucle contador de 1 minuto para hacer el MPO
        while i < 60:
            time.sleep(1)
            print("i vale: ",i)
            i += 1
            cursor.execute("SELECT finalizado FROM FIN_DE_MPO")
            result0 = cursor.fetchone()
            
            db.commit()
            
            print("FIN_DE_MPO vale:",result0[0])
            
            if result0[0] == 1:
                print("El MPO se completó antes")
                break
            else:
                #print("Se continua")
                #cursor.execute("SELECT finalizado FROM FIN_DE_MPO")
                #result0 = cursor.fetchone()
                print("Esperando realizacion del MPO")
                continue
                    
        print("Se acabó el tiempo")
        
        
        #Después del nuevo MPO, actualizo los valores de los MPOs       
        print("MPO finalizado")
        
        #Selecciono el nombre de la última persona que activó el autoelevador y que realizó el MPO
        cursor.execute("SELECT id, name FROM Usuarios WHERE rfid_uid = "+str(tagIDd))
        nombre_mpo = cursor.fetchone()
        
        #Aqui actualizo el campo usuario_mpo para indicar quien hizo el MPO en el turno
        cursor.execute("UPDATE USUARIO_MPO SET nombre = (%s)", (nombre_mpo[1],))
        print("Usuario que lo completó: ",nombre_mpo[1])
        db.commit()
        
        cursor.execute("SELECT mpo_1, mpo_2, mpo_3, mpo_7, mpo_8, mpo_9, mpo_10, habilitado FROM TABLA_MPO_1, TABLA_MPO_2, TABLA_MPO_3, HABILITACION ORDER BY TABLA_MPO_1.id DESC, TABLA_MPO_2.id DESC, TABLA_MPO_3.id DESC, HABILITACION.id DESC LIMIT 1")
        #cursor.execute("SELECT habilitado FROM habilitacion ORDER BY id DESC LIMIT 1")
        result1 = cursor.fetchone()
        mpo1=result1[0]
        mpo2=result1[1]
        mpo3=result1[2]
        mpo7=result1[3]
        mpo8=result1[4]
        mpo9=result1[5]
        mpo10=result1[6]
        habilitado=result1[7]
        
        #Uso cuenta para contar los 7 MPOs que me interesan (mpo1,mpo2,mpo3,mpo7,mpo8,mpo9,mpo10)
        cuenta= 0
        print("Habilitado: ")
        print(habilitado)
        if habilitado == 1:
            for i in result1:
                #print("i vale: ",i) 
                cuenta= cuenta + 1
                if i == 0:
                    resultado = 0
                    break

        else:
            print("No se completó el MPO todavía")

        #Resultado = 1 quiere decir que el MPO dió OK
        if (cuenta > 7):
            resultado = 1
          
        if resultado == 0:
            gpio.output(ReleAuto, gpio.LOW)
            print("MPO no OK, NO puede circular")
            cursor.execute("UPDATE FIN_DE_MPO SET finalizado='0'")
            db.commit()
            mpo = 0
            time.sleep(3)
        else:
            gpio.output(ReleAuto, gpio.HIGH)
            print("MPO OK, puede circular")
            cursor.execute("UPDATE FIN_DE_MPO SET finalizado='0'")
            db.commit()
            mpo = 1

            time.sleep(3)
        return
    
try:
    gpio.add_event_detect(Sensor, gpio.FALLING, callback=Cuenta, bouncetime=500)

    while True:
        Lectura_Tarjeta(1)
        if gpio.input(Sensor) == 1: #originalmente tiene que ser 1 la consulta
            print("Asiento desocupado")
            cursor.execute("UPDATE USUARIO_ACTIVO SET nombre = 'Unidad sin uso en este momento'")
            db.commit()
            gpio.output(ReleAuto, gpio.LOW)
            #gpio.output(ReleElo, gpio.LOW)  
        else:
            print("Usuario sentado")
            if bandera == 1 and mpo == 1:
                gpio.output(ReleAuto, gpio.HIGH)
                #gpio.output(ReleElo, gpio.HIGH)
            #gpio.output(ReleAuto, gpio.HIGH)
            #gpio.output(ReleElo, gpio.HIGH)
        time.sleep(1)

finally:
    gpio.add_event_detect(Sensor, gpio.FALLING, callback=Cuenta, bouncetime=500)
    while True:
        Lectura_Tarjeta(1)
        if gpio.input(Sensor) == 1:
            print("Asiento desocupado")
            cursor.execute("UPDATE USUARIO_ACTIVO SET nombre = 'Unidad sin uso en este momento'")
            db.commit()
            gpio.output(ReleAuto, gpio.LOW)
            #gpio.output(ReleElo, gpio.LOW)  
        else:
            print("Usuario sentado")
            if bandera == 1 and mpo == 1:
                gpio.output(ReleAuto, gpio.HIGH)
                #gpio.output(ReleElo, gpio.HIGH)
            #gpio.output(ReleAuto, gpio.HIGH)
            #gpio.output(ReleElo, gpio.HIGH)
        time.sleep(1)