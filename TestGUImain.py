from tkinter import *
# import tkinter
import cv2
from PIL import Image, ImageTk
from collections import deque
import WebcamExample as wc
import _thread as thread
# import goldilocksControlThreePumps as Goldilocks


class mainGUI:
	def __init__(self, master):
		self.master = master
		master.title("Mobile Fouling Setup")
		
		# self.firstLabelText = Label(master, font = 'bold 20', text="Goldilocks mobile fouling interface")
		# self.firstLabelText.grid(row = 1, column = 1)

		#Main Buttons
		
		#Homing
		self.homeButton = Button(master, text="Home all motors", background = 'green', foreground = 'white', font = 'bold', command = self.onHomePress)
		self.homeButton.grid(row = 8, column = 4, ipadx = 3, ipady = 20)

		#Number of syringes
		self.syringeLabel = Label(master, font = "bold 14", text="Number of syringes: ")
		self.syringeLabel.grid(row = 3, column = 1)
		self.oneSyringe = Button(master, font = "bold 14", text="1", relief = RAISED, command = self.onOneSyringePress)
		self.twoSyringe = Button(master, font = "bold 14", text="2", relief = RAISED, command = self.onTwoSyringePress)
		self.threeSyringe = Button(master, font = "bold 14", text = "3", relief = RAISED, command = self.onThreeSyringePress)

		self.oneSyringe.grid(row = 3, column = 2, ipadx = 3, ipady = 3)
		self.twoSyringe.grid(row = 3, column = 3, ipadx = 3, ipady = 3)
		self.threeSyringe.grid(row = 3, column = 4, ipadx = 3, ipady = 3)

		#Start or stop Formulation
		self.startFormulationButton = Button(master, text="START",background = 'green', foreground = 'white', font = 'bold', relief = RAISED, command = self.onStartFormulationPress)
		self.startFormulationButton.grid(row = 8, column = 2, ipadx = 3, ipady = 20)
		self.stopFormulationButton = Button(master, text="STOP",background = 'red', foreground = 'white', font = 'bold', relief = RAISED, command = self.onStopFormulationPress)
		self.stopFormulationButton.grid(row = 8, column = 3, ipadx = 3, ipady = 20)

		#Output filename
		Label(text = "Filename: ", font = 'bold 14').grid(row = 3, column = 5, ipadx = 3, ipady = 20)
		self.filename = Entry(master)
		self.filename.grid(row = 3, column = 6)		
		self.filename.delete(0, END) #Start index 0 till the END - defined by Tinker class
		self.filename.insert(0, "Enter filename")

#Pump values
# vcmd = master.register(self.validate) # we have to wrap the command
# self.entry = Entry(master, validate="key", validatecommand=(vcmd, '%P'))
	
		syringe_sizes = list(("5", "10", "20", "30", "50", "60", "140"))
		horizontal_labels = list(("Speed (ml/min)", "Dispense Volume (ml)", "Syringe Size (ml)")) 
		vertical_labels = list(("Syringe 1", "Syringe 2", "Syringe 3"))

		i = 2
		for c in horizontal_labels:
			Label(font = "bold 14", relief = 'ridge', text = c).grid(row = 4, column = i, ipadx = 3, ipady = 10)
			i = i + 1
		j = 5
		for c in vertical_labels:
			Label(font = "bold 14", text = c).grid(row = j, column = 1, ipadx = 3, ipady = 5)
			j = j + 1

#Syringe 1

		self.s1Speed_box = Entry(master)
		self.s1Speed_box.grid(row = 5, column = 2)
		self.s1Speed_box.delete(0, END) #Start index 0 till the END - defined by Tinker class
		self.s1Speed_box.insert(0, "0")
		self.s1Vol_box = Entry(master)
		self.s1Vol_box.grid(row = 5, column = 3)
		self.s1Vol_box.delete(0, END) #Start index 0 till the END - defined by Tinker class
		self.s1Vol_box.insert(0, "0")
		self.syringe_size1 = IntVar(master)
		self.syringe_size1.set(syringe_sizes[1])
		self.syringe1SizeDropdown = OptionMenu(master, self.syringe_size1, *syringe_sizes)	
		self.syringe1SizeDropdown.grid(row = 5, column = 4)

#Syringe 2

		self.s2Speed_box = Entry(master)
		self.s2Speed_box.grid(row = 6, column = 2)
		self.s2Speed_box.delete(0, END) #Start index 0 till the END - defined by Tinker class
		self.s2Speed_box.insert(0, "0")
		self.s2Vol_box = Entry(master)
		self.s2Vol_box.grid(row = 6, column = 3)
		self.s2Vol_box.delete(0, END) #Start index 0 till the END - defined by Tinker class
		self.s2Vol_box.insert(0, "0")
		self.syringe_size2 = IntVar(master)
		self.syringe_size2.set(syringe_sizes[1])
		self.syringe2SizeDropdown = OptionMenu(master, self.syringe_size2, *syringe_sizes)	
		self.syringe2SizeDropdown.grid(row = 6, column = 4)

#Syringe 3

		# syringeFrame = Frame(self.master, padx = 3, pady = 3)
		self.s3Speed_box = Entry(master)
		self.s3Speed_box.grid(row = 7, column = 2)
		self.s3Speed_box.delete(0, END) #Start index 0 till the END - defined by Tinker class
		self.s3Speed_box.insert(0, "0")
		self.s3Vol_box = Entry(master)
		self.s3Vol_box.grid(row = 7, column = 3)
		self.s3Vol_box.delete(0, END) #Start index 0 till the END - defined by Tinker class
		self.s3Vol_box.insert(0, "0")
		self.syringe_size3 = IntVar(master)
		self.syringe_size3.set(syringe_sizes[1])
		self.syringe3SizeDropdown = OptionMenu(master, self.syringe_size3, *syringe_sizes)	
		self.syringe3SizeDropdown.grid(row = 7, column = 4)

		# syringeFrame.pack(fill = X) #X direction - each element added goes across the screen

		# self._syringeValues()

	# 		#### Camera
	# 	image_label = Label(master=root)# label for the video frame
	# 	image_label.grid(row = 1, column = 8)
	# 	cam = cv2.VideoCapture(1) 
	# 	fps_label = Label(master=root)# label for fps
	# 	fps_label._frame_times = deque([0]*5)  # arbitrary 5 frame average FPS
	# 	fps_label.grid(row = 1, column = 7)
	# 	# quit button
	# 	quit_button = Button(master=root, text='Quit',command=lambda: quit_(root))
	# 	quit_button.grid(row = 1, column = 9)
	# 	# setup the update callback
	# 	root.after(0, func=lambda: self.update_all(root, image_label, cam, fps_label))
	# ### END Camera


	def validate(self, new_text):
		if not new_text: # the field is being cleared
		    self.entered_number = 0
		    return True
		try:
		    self.entered_number = int(new_text)
		    return True
		except ValueError:
		    return False

	def onHomePress(self):
		print("Homing")
		#run homing here

	def onOneSyringePress(self):
		num_syringe = 1
		self.oneSyringe.config(relief = SUNKEN, background = 'green2')
		self.twoSyringe.config(relief = RAISED, background = 'SystemButtonFace')
		self.threeSyringe.config(relief = RAISED, background = 'SystemButtonFace')
		print("Syringes: " + str(num_syringe))

	def onTwoSyringePress(self):
		num_syringe = 2
		self.oneSyringe.config(relief = RAISED, background = 'SystemButtonFace')
		self.twoSyringe.config(relief = SUNKEN, background = 'green2')
		self.threeSyringe.config(relief = RAISED, background = 'SystemButtonFace')
		print("Syringes: " + str(num_syringe))

	def onThreeSyringePress(self):
		num_syringe = 3
		self.oneSyringe.config(relief = RAISED, background = 'SystemButtonFace')
		self.twoSyringe.config(relief = RAISED, background = 'SystemButtonFace')
		self.threeSyringe.config(relief = SUNKEN, background = 'green2')
		print("Syringes: " + str(num_syringe))

	def _syringeValues(self, master):
		#syringe volume and speed selector
		#	Input text box
		#	
		#button to turn on/off

		syringeFrame = Frame(self.master, padx = 3, pady = 3)
		syringeFrame.pack(fill = X) #X direction - each element added goes across the screen

		self.s1Speed_box = Entry(syringeFrame)
		self.s1Speed_box.pack(side = LEFT)

		self.s1Speed_box.delete(0, END) #Start index 0 till the END - defined by Tinker class
		self.s1Speed_box.insert(0, "Type in LED number")
		# self.ledID_Button = Button(ledFrame, text = "Set LED", command = self._on_ledID_button)
		# self.ledID_Button.pack()

	def onStartFormulationPress(self):
		print("Starting Formulation")
		thread.start_new_thread(self.Goldilocks, ())

	def onStopFormulationPress(self):
		print("Stopping")

if __name__ == "__main__":

	root = Tk()
	main_GUI = mainGUI(root)
	root.mainloop()