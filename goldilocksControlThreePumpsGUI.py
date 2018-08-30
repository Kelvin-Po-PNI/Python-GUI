'''
Date: 04/06/2018
Author: Chuan Du

Take user input of syringe size (mL), volume to dispense (mL), and flowrate (mL/min), calculate the velocity and steps to travel, write as a command in Arduino serial.
Whenever user requests stop by pressing any key on the keybaord (eg. q), the pumps will terminate.

Date: 04/15/2018
Change the goldilocks control into a class with proper lower case underscore python syntax.
Requires Python 3.x
'''
#import libraries
import serial
import serial.tools.list_ports
from serial.serialutil import SerialException
import time
import datetime
import math
import sys
import _thread as thread
import msvcrt

class goldilocks_control:
    # ==== definitions ==================================================
    commands = {"startUp": "1", "powerUp": "2", "getPressure": "40", "endPressure": "41", "findHome": "10", "syringeDetect": "11", "formulate": "12", "idleCheck": "14","stopMotor": "15"}
    baudrate = 57600
    DEBUG = True
    stop_requested = False

    #constructor
    def __init__(self):
        # ==== syringe info ====
        self.syringe_volumes = [] # [syringe 1, syringe 2, syringe 3]
        self.flow_rates = [] # mL/min
        self.vol_to_dispense = []
        self.formulation_times = [] #calculate based on flow_rate and vol_to_dispense to obtain formulation time in seconds
        #self.initFlag = False connect to arduino flag

    def get_formulation_time(self, flow_rate, vol_to_dispense):
        """returns the formulation time in seconds given flow rate and volume to dispense"""
        return float(vol_to_dispense) / float(flow_rate) * 60.0
    # ==== Motor travel calculation ==================================================

    def volume_to_diameter(self, syringe_size):
        """Maps syringe size (mL) to internal diameter (mm)"""
        # syringe diameter (mm)
        diams = {5: 12.06, 10: 14.5, 20: 19.13, 30: 21.70, 50: 26.7, 60: 26.162, 140: 37.61}
        #changed 60ml syringe diameter from 26.7 to 26.162
        #print (diams[int(syringe_size)])
        return diams[int(syringe_size)]

    #currently not using in code.
    def volume_to_maxTravel(self, syringe_size):
        """Given syringe size (mL), map it to maximum amount of travel before motor stops trying to detect a syringe"""
        #attn: need to calculate different values for 50 mL, 60 mL, and 140 mL syringes (shorter distance)
        maxTravel = {5: 2850000, 10: 2350000, 20: 1950000, 30: 1650000, 50: 1650000, 60: 1650000, 140: 1650000}
        return maxTravel[int(syringe_size)]

    def volume_to_microstep(self, syringe_size, vol_to_dispense):
        """calculate the number of microsteps to travel in order to dispense a volume"""
        #lead screw = 2 mm, 1.8 deg motor, 256 microsteps/revolution
        syringe_diameter = self.volume_to_diameter(syringe_size)

        # step_size = 0.0000390625 # in mm
        # 2 mm / (360/1.8) / 256
        step_size = 0.0000390625
        syringe_area = 0.25 * 3.14 * (syringe_diameter) * (syringe_diameter) # mm^2
        step_length = 1000 * float(vol_to_dispense) / syringe_area # 1000 mm^3/ml * ml / mm^2 = mm
        steps = step_length / step_size # mm/mm
        #print(steps)
        steps = self.round_to_int(steps)
        #steps = self.round_to_int(steps)
        #print(steps)
        return steps

    def flow_to_velocity(self,syringe_size, flow_rate):
        """convert flow rate (mL/min) to velocity (steps/sec)"""
        steps_per_mL = self.volume_to_microstep(syringe_size, 1)

        steps_per_sec = self.round_to_int(float(flow_rate) * steps_per_mL / 60.0)
        return steps_per_sec

    #to be used
    def formualtion_param_update(self, syringe_vol, flow_rate, vol_to_dispense):
        #may come in handy with GUI
        self.syringe_volumes = syringe_vol
        self.flow_rates = flow_rate
        self.vol_to_dispense = vol_to_dispense




    # # ==== motor communication ================================================== ORIGINAL
    # def syringe_idle_status(self, all=False):

    #     allSyringeReady = True

    #     if all:
    #         pusher_idx = range(3)
    #     else:
    #         pusher_idx = range(len(self.syringe_volumes))

    #         for i in pusher_idx:
    #             self.ser.reset_input_buffer()
    #             self.ser.reset_output_buffer()
    #             #time.sleep(0.1) this delay is not necessary

    #             pusherAddress = str(i + 1)
    #             queryCommand = "QR"
    #             #serial write talks to arduino
    #             #14,/1QR;
    #             self.ser.write((self.commands["idleCheck"]+ ",/" + pusherAddress + queryCommand + ";").encode("utf-8"))
    #             #print(self.commands["idleCheck"]+ ",/" + pusherAddress + queryCommand + ";")
    #             time.sleep(0.1)

    #             line = self.ser.readline()
    #             print(line)

    #         # if '`` is not in the reply, we know at least one motor is busy
    #         if b'`' not in line:
    #             allSyringeReady = False

    #     return allSyringeReady


        ########################################################################################### Jessica's

    def syringe_idle_status(self, all=False):

        allSyringeReady = False

        if all:
            pusher_idx = range(3)
        else:
            pusher_idx = range(len(self.syringe_volumes))

            for i in pusher_idx:
                self.ser.reset_input_buffer()
                self.ser.reset_output_buffer()
                #time.sleep(0.1) this delay is not necessary

                pusherAddress = str(i + 1)
                queryCommand = "QR"
                #serial write talks to arduino
                #14,/1QR;
                self.ser.write((self.commands["idleCheck"]+ ",/" + pusherAddress + queryCommand + ";").encode("utf-8"))
                #print(self.commands["idleCheck"]+ ",/" + pusherAddress + queryCommand + ";")
                time.sleep(0.1)

                line = self.ser.readline()
                print(line)

                # if '`` is not in the reply, we know at least one motor is busy
                if b'`' not in line:
                    allSyringeReady = False
                    break

                else:
                    allSyringeReady = True

        return allSyringeReady



        ###########################################################################################

    def write_to_pushers_individually(self, protocol, command):
        """write a command to each active pusher in sequence"""
        #if command is not a list (just a single string)
        #give command to all active pushers by creating a list of the same commands
        #write as many commands as there are syringe volumes in the list
        if not isinstance(command, list):
            command = [command]*len(self.syringe_volumes)

        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()

        #time.sleep(0.1)
        pusher_idx = range(len(self.syringe_volumes))

        # iterate through 2 lists of same length
        for i, cmd in zip(pusher_idx, command):
            #syringe pump 1 is address 0+1 = 1
            #syringe pump 2 is address 1+1 = 2
            #syringe pump 3 is address 2+1 = 3
            pusherAddress = str(i + 1)
            self.ser.write((self.commands[protocol] + ",/" + pusherAddress + cmd + ";").encode("utf-8"))

        time.sleep(0.1)

    def round_to_int(self,num):
        return int(num + 0.5)

    def reset_all(self):
        global stop_requested
        stop_requested = False

        # order of operations
        # 1. set all motor currents to 75%
        # 2. home all motors
        # 3. set motors to default speed
        step = 1.0
        while stop_requested == False:
            if (step == 1.0):
                find_home()
                time.sleep(0.1)
                step += 0.5
                continue
            elif (step == 2.0):
                break
            else:
                if (syringe_idle_status()):
                    print("motor is free")
                    step += 0.5
                    time.sleep(0.1)
                continue

        self.stop_motor()
    #link with GUI button
    def request_stop(self):
        global stop_requested
        stop_requested = True
        return

    def power_up(self):
        self.ser.reset_input_buffer()
        #set power for all syringe pumps
        command = "m75R"
        self.write_to_pushers_individually("powerUp", command)
        time.sleep(0.1)
        self.ser.flush()

    def start_up(self):
        #same for all active syringe pumps
        #convert both opto switches to limit switches "n2f1"
        #F1 sets the direction considered as positive for the motor
        #move slightly away from home and then move until home switch is detected.
        self.ser.reset_input_buffer()
        startUpCommand = "/_n2f1m75F1V100000P20000V100000Z5000000R"
        #write directly
        self.ser.write((self.commands["startUp"]+ "," + startUpCommand + ";").encode("utf-8"))
        time.sleep(0.1)
        self.ser.flush()

    def syringe_detect(self):
        #same for all active syringe pumps
        #move relative to forward direction until syringe is detected
        #configure limit switches
        self.ser.reset_input_buffer()
        #syringeDetectCommand = "/1n2m75V200000P0n0P25600R"
        syringeDetectCommand = "n2m75V200000P0n0P25600R"
        self.write_to_pushers_individually("syringeDetect", syringeDetectCommand)
        time.sleep(0.1)

        ############## Wait to make sure all motors are idle before proceeding

        idleStatus = self.syringe_idle_status()
        print("First read: ", idleStatus)
        while (idleStatus == False):
            idleStatus = self.syringe_idle_status()
            print("Second read: ", idleStatus)
            time.sleep(0.1)
        
        ##############

        #ser.write((commands["syringeDetect"]+ "," + syringeDetectCommand + ";").encode("utf-8"))

        self.ser.flush()

    def find_home(self):
        # homeCommand = "/1n2V100000D0R"
        #reconfigure limit switches
        self.ser.reset_input_buffer()
        findHomeCommand = "/_n2V100000D0R"
        self.ser.write((self.commands["findHome"]+ "," + findHomeCommand + ";").encode("utf-8"))
        time.sleep(0.1)
        self.ser.flush()

    def do_formulation(self):

        global stop_requested
        stop_requested = False

        syringe_volumes = self.syringe_volumes
        flow_rates = self.flow_rates

        microsteps = [] #travel distance, defined by syringe volumeToDispense
        velocity = [] #velocity of syringes, defined by input parameters
        stop = [] # use vol_to_maxTravel to determine stopping distance

        #determine length and stopping point for each syringe
        for sy_volume, dispense in zip(self.syringe_volumes, self.vol_to_dispense):
            microsteps.append(self.volume_to_microstep(sy_volume, dispense))
            stop.append(self.volume_to_maxTravel(sy_volume))

        #determine speed of each syringe based on input flow parameters
        for fr, sy_volume in zip(self.flow_rates, self.syringe_volumes):
            velocity.append(self.flow_to_velocity(sy_volume, fr))

        # main iterables
        # iterate through the following steps. Syringe idleness and stop requests are checked
        # at every iteration.
        # 1. start up commands which homes all motors
        # 2. turn off all motors
        # 3. turn on active syringe pump motors
        # 4. active syringe pumps find syringe
        # 5. formulate
        # 6. find home
        # 7. close serial port?
        step = 1.0
        while stop_requested == False:
            if (step == 1.0):
                print("Starting up all syringe pumps...")
                self.start_up()
                time.sleep(0.1)
                step += 0.5
                continue

            elif (step == 2.0):
                print("turning off all motors")
                self.stop_motor()
                time.sleep(0.1)
                step += 0.5
                continue

            elif(step == 3.0):
                print("tuning on active syringe pump motors")
                self.power_up()
                time.sleep(0.1)
                step += 0.5
                continue

            elif (step == 4.0):
                #only write command to the number of syringes requested by user
                print("Working on finding syringes")
                #time.sleep(1)
                self.syringe_detect()
                time.sleep(0.1)
                step += 0.5
                continue

            elif (step == 5.0):
                print("start formulation")
                #very important
                self.ser.reset_input_buffer()
                time.sleep(0.1)
                #self.ser.reset_output_buffer()

                formulateCmd = []
                for x in range (0, len(self.syringe_volumes)):
                    #v = self.flow_to_velocity(self.syringe_volumes(x), self.flow_rates(x))
                    #p = self.volume_to_microstep(self.syringe_volumes(x), self.vol_to_dispense(x))
                    formulateCmd.append("n0z0"+ "V" + str(velocity[x]) + "A" + str(microsteps[x]) + "R")

                self.write_to_pushers_individually("formulate", formulateCmd)
                time.sleep(0.1)

                step += 1.0 #go straight to pressure collection
                continue

            elif (step == 6.0):
                self.gen_pressure_file()
                time.sleep(0.1)
                step += 1.0
                continue

            elif (step == 7.0):
                print("end pressure collection")
                self.end_pressure()
                time.sleep(0.1)
                step += 0.5
                continue

            elif (step == 8.0):
                print("Resetting to home position")
                time.sleep(10)
                self.find_home()
                time.sleep(0.1)
                step += 0.5
                continue

            elif (step == 9.0):
                print("success")
                break

            else:
                if (self.syringe_idle_status()):
                    print("motor is free")
                    print(datetime.datetime.now().time())
                    step += 0.5
                    #time.sleep(0.1)
                # else:
                #     print("waiting")
                continue

            self.stop_motor()
            time.sleep(1)
            #ser.close()

    def stop_motor(self):
        self.ser.reset_input_buffer()
        stopCommand = "/_Tm0R"
        self.ser.write((self.commands["stopMotor"]+ "," + stopCommand + ";").encode("utf-8"))
        time.sleep(0.1)
        print("stop motor command sent")
        self.ser.flush()

    def input_thread(self):
        msvcrt.getch()
        thread.interrupt_main()

    def main(self):
        try:
            thread.start_new_thread(self.input_thread, ())
            print("executing main.")
            self.do_formulation()

        except KeyboardInterrupt:
            global stop_requested
            stop_requested = True
            self.stop_motor()
            self.stop_motor()

        self.stop_motor()

    # ==== functions =====
    def time_is_up(self, start_time, interval):
        current_time = time.time()
        if((current_time - start_time) > interval):
            print(current_time - start_time)
            return True
        else:
            return False

    def get_pressure(self):
        self.ser.reset_input_buffer()
        self.ser.write((self.commands["getPressure"] + "," + str(max(self.formulation_times) + 5.0) + ";").encode("utf-8"))
        #sleep for 10 milisecond
        time.sleep(0.01)
        self.ser.flush()

    def end_pressure(self):

        self.ser.reset_input_buffer()
        self.ser.write((self.commands["endPressure"] + ";").encode("utf-8"))
        print((self.commands["endPressure"] + ";" + str(max(self.formulation_times) + 5.0)))
        #sleep for 10 milisecond
        time.sleep(0.01)
        self.ser.flush()

    # ==== pressure file ===
    def gen_pressure_file(self):
        #print("in pressure file")
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()

        time_now = datetime.datetime.now()
        time_str = str(time_now)
        file_name = "pressure data " + time_str.replace(":","-") + ".txt"
        #create text file to write data, w = write

        self.get_pressure()

        with open(file_name, 'w') as fname:
            header1 = "#TIMESTAMP, TIME(s), PRESSURE_1(PSI), PRESSURE_2(PSI)"
            fname.write(header1 + "\n")

            exited = False

            #start_time = float(time.time())
            #interval = float(max(self.formulation_times) + 5.0) # add 5 seconds after calculated formulation time

            #while(exited == False and not self.time_is_up(start_time, interval)):
            while(exited == False):
                try:
                    data = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    data += ","

                    try:
                        serialExceptionOccured = False

                        try:
                            analog_reading = bytes.decode(self.ser.readline())
                        except:
                            analog_reading = "can't decode \n"

                        if len(analog_reading) <= 1:
                            serialExceptionOccured = True

                        if "time is up" in analog_reading:
                            exited = True

                    except serial.SerialTimeoutException:
                        serialExceptionOccured = True

                    if exited == False and not serialExceptionOccured:
                        data += analog_reading
                        fname.write (data)
                        time.sleep(0.05)

                        print(data)
                        #self.ser.reset_input_buffer()
                        #self.ser.reset_output_buffer()

                    # if (self.syringe_idle_status()):
                    #     exited = True

                    # self.ser.reset_input_buffer()
                    # print (data)

                except (KeyboardInterrupt, SystemExit):
                    if self.ser.closed==False:
                        #self.ser.close()
                        exited=True
                    else:
                        exited=True

        print("done")
        time.sleep(1)

    # ==== syringe pump parameters ====

    def syringe_pump_I(self, size, rate, vol):
        print("SYRINGE PUMP I")
        syringe_size1 = size #input("syringe size (mL): ")
        flow_rate1 = rate #input("flow rate (mL/min): ")
        vol_to_dispense1 = vol #input("volume to dispense (mL): ")

        self.syringe_volumes.append(syringe_size1)
        self.flow_rates.append(flow_rate1)
        self.vol_to_dispense.append(vol_to_dispense1)
        self.formulation_times.append(self.get_formulation_time(flow_rate1, vol_to_dispense1))

    def syringe_pump_II(self):
        print("SYRINGE PUMP II")
        syringe_size2 = input("syringe size (mL): ")
        flow_rate2 = input("flow rate (mL/min): ")
        vol_to_dispense2 = input("volume to dispense (mL): ")

        self.syringe_volumes.append(syringe_size2)
        self.flow_rates.append(flow_rate2)
        self.vol_to_dispense.append(vol_to_dispense2)
        self.formulation_times.append(self.get_formulation_time(flow_rate2, vol_to_dispense2))

    def syringe_pump_III(self):
        print("SYRINGE PUMP III")
        syringe_size3 = input("syringe size (mL): ")
        flow_rate3 = input("flow rate (mL/min): ")
        vol_to_dispense3 = input("volume to dispense (mL): ")

        self.syringe_volumes.append(syringe_size3)
        self.flow_rates.append(flow_rate3)
        self.vol_to_dispense.append(vol_to_dispense3)
        self.formulation_times.append(self.get_formulation_time(flow_rate3, vol_to_dispense3))

# assume 1 syringe pump = address 1
#        2 syringe pumps = addresses 1 and 2 (not 1 and 3 or 2 and 3)
#        3 syringe pumps = addresses 1, 2, 3


################################## put in function in a separate init function to deal with arduino first. Do that and the GUI should pop up
# beginning of testing: if not initialized, begin with this


# def initArduino(self):
    # ==== find COM port for arduino ====
    ports = list(serial.tools.list_ports.grep("arduino"))
    #print(ports)

    if len(ports) == 1:
        print("Arduino found.")
    else:
        print("Arduino not found or too many of them.")
        print("Check Arduino connection and whether drivers are installed.")
        sys.exit()

    # connect to com port
    arduinoPort = ports[0]
    ser = serial.Serial(arduinoPort[0], timeout = 0.1, baudrate = baudrate)
    #print(ser)
    print ("connected to arduino at " + str(arduinoPort))
    #sleep for 2 seconds
    time.sleep(2)
##################################



####################################All this goes in the init/begin testing function
#if (not initialized):
    #self.init()
    #self.initFlag = True



gold = goldilocks_control()

# rehome = input("Re-home motors? y/n: ")
# if (rehome == "y" or rehome == "yes" or rehome == "Yes" or rehome == "YES"):
#     gold.start_up()
#     time.sleep(0.1)
#     gold.stop_motor()
#     time.sleep(0.1)
#     gold.power_up()
#     time.sleep(1)
#     gold.find_home()

# print("==== Goldilocks Syringe Pumps ====")
# num_syringe = input("number of syringe pumps (1, 2, or 3), or 0 to exit: ")

# if (num_syringe == "1"):
#     gold.syringe_pump_I()
# elif(num_syringe == "2"):
#     gold.syringe_pump_I()
#     gold.syringe_pump_II()
# elif(num_syringe == "3"):
#     gold.syringe_pump_I()
#     gold.syringe_pump_II()
#     gold.syringe_pump_III()
# elif(num_syringe == "0"):
#     sys.exit()

if(gold.DEBUG):
    print(gold.formulation_times)
#######################################################################################
#pressure_file_name = input("Please enter file name: ")
# material_1 = input("Material 1: ")
# material_2 = input("Material 2: ")

# gold.stop_motor()
# time.sleep(1)

# gold.main()
# time.sleep(1)
# gold.find_home()
