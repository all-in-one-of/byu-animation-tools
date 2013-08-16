from PyQt4.QtCore import *
from PyQt4.QtGui import *

import maya.cmds as cmd
import maya.OpenMayaUI as omu
import sip
import os, glob
import utilities as amu

CHECKOUT_WINDOW_WIDTH = 330
CHECKOUT_WINDOW_HEIGHT = 600

def maya_main_window():
	ptr = omu.MQtUtil.mainWindow()
	return sip.wrapinstance(long(ptr), QObject)		

class CheckoutDialog(QDialog):
	def __init__(self, parent=maya_main_window()):
	#def setup(self, parent):
		QDialog.__init__(self, parent)
		self.setWindowTitle('Checkout')
		self.setFixedSize(CHECKOUT_WINDOW_WIDTH, CHECKOUT_WINDOW_HEIGHT)
		self.create_layout()
		self.create_connections()
		self.refresh()
	
	def create_layout(self):
		#Create the selected item list
		self.selection_list = QListWidget()
		self.selection_list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

		#Create Models, Rig, Animation		
		radio_button_group = QVBoxLayout()
		self.model_radio = QRadioButton('Model')
		self.rig_radio = QRadioButton('Rig')
		self.animation_radio = QRadioButton('Animation')
		self.model_radio.setChecked(True)
		radio_button_group.setSpacing(2)
		radio_button_group.addWidget(self.model_radio)
		radio_button_group.addWidget(self.rig_radio)
		radio_button_group.addWidget(self.animation_radio)

		#Create New Animation button
		self.new_animation_button = QPushButton('New Animation')
		
		#Create Unlock button
		self.unlock_button = QPushButton('Unlock')

		#Create Select and Cancel buttons
		self.select_button = QPushButton('Select')
		self.info_button = QPushButton('Get Info')
		self.cancel_button = QPushButton('Cancel')
		
		#Create button layout
		button_layout = QHBoxLayout()
		button_layout.setSpacing(2)
		button_layout.addStretch()
	
		button_layout.addWidget(self.select_button)
		button_layout.addWidget(self.info_button)
		button_layout.addWidget(self.unlock_button)
		button_layout.addWidget(self.cancel_button)
		
		#Create main layout
		main_layout = QVBoxLayout()
		main_layout.setSpacing(2)
		main_layout.setMargin(2)
		main_layout.addWidget(self.selection_list)		
		main_layout.addLayout(radio_button_group)
		main_layout.addWidget(self.new_animation_button)
		main_layout.addLayout(button_layout)
		
		self.setLayout(main_layout)
	
	def create_connections(self):
		#Connect the selected item list widget
		self.connect(self.selection_list,
					SIGNAL('currentItemChanged(QListWidgetItem*, QListWidgetItem*)'),
					self.set_current_item)
			
		#Connect the buttons
		self.connect(self.model_radio, SIGNAL('clicked()'), self.refresh)
		self.connect(self.rig_radio, SIGNAL('clicked()'), self.refresh)
		self.connect(self.animation_radio, SIGNAL('clicked()'), self.refresh)
		self.connect(self.new_animation_button, SIGNAL('clicked()'), self.new_animation)
		self.connect(self.unlock_button, SIGNAL('clicked()'), self.unlock)
		self.connect(self.select_button, SIGNAL('clicked()'), self.checkout)
		self.connect(self.info_button, SIGNAL('clicked()'), self.show_node_info)
		self.connect(self.cancel_button, SIGNAL('clicked()'), self.close_dialog)
	
	def update_selection(self, selection):
		#Remove all items from the list before repopulating
		self.selection_list.clear()
		
		#Add the list to select from
		for s in selection:
			item = QListWidgetItem(os.path.basename(s)) 
			item.setText(os.path.basename(s))
			self.selection_list.addItem(item)
		self.selection_list.sortItems(0)
	
	def refresh(self):
		if self.animation_radio.isChecked():
			self.new_animation_button.setEnabled(True)
			selections = glob.glob(os.path.join(os.environ['SHOTS_DIR'], '*'))
		else:
			self.new_animation_button.setEnabled(False)
			selections = glob.glob(os.path.join(os.environ['ASSETS_DIR'], '*'))
		self.update_selection(selections)
	
	def new_animation(self):
		text, ok = QInputDialog.getText(self, 'New Animation', 'Enter seq_shot (ie: a01)')
		if ok:
			text = str(text)
			amu.createNewShotFolders(os.environ['SHOTS_DIR'], text)
		self.refresh()
		return
	
	def get_filename(self, parentdir):
		return os.path.basename(os.path.dirname(parentdir))+'_'+os.path.basename(parentdir)

	def showIsLockedDialog(self):
		return cmd.confirmDialog(title = 'Already Unlocked'
                                , message       = 'Asset already unlocked'
                                , button        = ['Ok']
                                , defaultButton = 'Ok'
                                , cancelButton  = 'Ok'
                                , dismissString = 'Ok')

	def showConfirmUnlockDialog(self):
		return cmd.confirmDialog( title = 'Confirmation'
                                 , message       = 'Are you sure you want to unlock this asset?'
                                 , button        = ['Yes', 'No']
                                 , defaultButton = 'No'
                                 , cancelButton  = 'No'
                                 , dismissString = 'No')

	def showUnlockedDialog(self):
		return cmd.confirmDialog(title    = 'Asset unlocked'
		           , message       = 'Asset unlocked'
		           , button        = ['Ok']
		           , defaultButton = 'Ok'
		           , cancelButton  = 'Ok'
		           , dismissString = 'Ok')


	def unlock(self):

		asset_name = str(self.current_item.text())

		if self.model_radio.isChecked():
			toUnlock = os.path.join(os.environ['ASSETS_DIR'], asset_name, 'model')
		elif self.rig_radio.isChecked():
			toUnlock = os.path.join(os.environ['ASSETS_DIR'], asset_name, 'rig')
		elif self.animation_radio.isChecked():
			toUnlock = os.path.join(os.environ['SHOTS_DIR'], asset_name, 'animation')
		
		if amu.isLocked(toUnlock):

			if self.showConfirmUnlockDialog() == 'No':
				return
			
			cmd.file(save=True, force=True)
			cmd.file(force=True, new=True) #open new file
			amu.unlock(toUnlock)
			self.showUnlockedDialog()
				
		else:
			self.showIsLockedDialog()

	
	########################################################################
	# SLOTS
	########################################################################
	def checkout(self):
		curfilepath = cmd.file(query=True, sceneName=True)
		if not curfilepath == '':
			cmd.file(save=True, force=True)

		asset_name = str(self.current_item.text())
		if self.model_radio.isChecked():
			toCheckout = os.path.join(os.environ['ASSETS_DIR'], asset_name, 'model')
		elif self.rig_radio.isChecked():
			toCheckout = os.path.join(os.environ['ASSETS_DIR'], asset_name, 'rig')
		elif self.animation_radio.isChecked():
			toCheckout = os.path.join(os.environ['SHOTS_DIR'], asset_name, 'animation')

		try:
			destpath = amu.checkout(toCheckout, True)
		except Exception as e:
			print str(e)
			if not amu.checkedOutByMe(toCheckout):
				cmd.confirmDialog(  title          = 'Can Not Checkout'
                                   , message       = str(e)
                                   , button        = ['Ok']
                                   , defaultButton = 'Ok'
                                   , cancelButton  = 'Ok'
                                   , dismissString = 'Ok')
				return
			else:
				destpath = amu.getCheckoutDest(toCheckout)

		toOpen = os.path.join(destpath, self.get_filename(toCheckout)+'.mb')
		
		# open the file
		if os.path.exists(toOpen):
			cmd.file(toOpen, force=True, open=True)#, loadReferenceDepth="none")
		else:
			# create new file
			cmd.file(force=True, new=True)
			cmd.file(rename=toOpen)
			cmd.file(save=True, force=True)
		self.close_dialog()
	
	def close_dialog(self):
		self.close()
	
	def set_current_item(self, item):
		self.current_item = item
		
	def show_node_info(self):
		asset_name = str(self.current_item.text())
		if self.model_radio.isChecked():
			filePath = os.path.join(os.environ['ASSETS_DIR'], asset_name, 'model')
		elif self.rig_radio.isChecked():
			filePath = os.path.join(os.environ['ASSETS_DIR'], asset_name, 'rig')
		elif self.animation_radio.isChecked():
			filePath = os.path.join(os.environ['SHOTS_DIR'], asset_name, 'animation')
		node_info = amu.getVersionedFolderInfo(filePath)
		checkout_str = node_info[0]
		if(checkout_str ==''):
			checkout_str = 'Not checked out. '
		else:
			checkout_str = 'Checked out by '+node_info[0]+'. '
		checkin_str = 'Last checked in by '+node_info[1]+' on '+node_info[2]
		cmd.confirmDialog(  title          = asset_name+" Info"
                                   , message       = checkout_str+checkin_str
                                   , button        = ['Ok']
                                   , defaultButton = 'Ok'
                                   , cancelButton  = 'Ok'
                                   , dismissString = 'Ok')
		
def go():
	dialog = CheckoutDialog()
	dialog.show()
	
if __name__ == '__main__':
	go()
	
	
	
	
	
	
	
	
	
	
