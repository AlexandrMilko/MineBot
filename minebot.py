import kivy
import time
import socket
import bot
import threading
import json
from bot import Bot # DO NOT DELETE THIS LINE. IS USED WITHIN exec() func

from kivy.uix.gridlayout import GridLayout
from kivymd.app import MDApp
from kivymd.theming import ThemeManager
from kivymd.uix.expansionpanel import MDExpansionPanel, MDExpansionPanelOneLine
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivy.uix.scrollview import ScrollView
from kivymd.uix.list import OneLineAvatarListItem, OneLineAvatarIconListItem
from kivy.properties import StringProperty

kivy.require('2.0.0')

COMMANDS_DELAY = 0.1

class CommandMove:
    def __init__(self, **kwargs): # MAKE name A CLASS VARIABLE!!!
        self.name = 'Move'

class CommandChat:
    def __init__(self, **kwargs):
        self.name = 'Chat'

class ConnectBotCommand:
    def __init__(self, **kwargs):
        self.name = 'Connect Bot'

class DelayCommand:
    def __init__(self, **kwargs):
        self.name = 'Delay'

class PlaceBlockCommand:
    inside_block = False
    hand = bot.PlayerBlockPlacementPacket.Hand.MAIN
    def __init__(self, **kwargs):
        self.name = 'Place Block'

class ForLoopStartCommand:
    def __init__(self, **kwargs):
        self.name = 'For Loop Start'

class ForLoopEndCommand:
    def __init__(self, **kwargs):
        self.name = 'For Loop End'

class UseCurrentItemCommand:
    hand = "MAIN"
    def __init__(self, **kwargs):
        self.name = 'Use Current Item'

class DigBlockCommand:
    def __init__(self, **kwargs):
        self.name = 'Dig Block'

# Commands' content
class MoveContent(GridLayout):
    pass

class ConnectBotContent(GridLayout):
    pass

class ChatContent(GridLayout):
    pass

class DelayContent(GridLayout):
    pass

class PlaceBlockContent(GridLayout):
	pass

class ForLoopStartContent(GridLayout):
    pass

class DigBlockContent(GridLayout):
    pass

# Popups And Other
class PopupContent(ScrollView):
    pass

class CommandPopup(MDDialog):
    pass

class SavePopupContent(ScrollView):
    pass

class SavePopupContent(ScrollView):
    pass

class ButtonOK(MDRaisedButton):
    pass

class Script(OneLineAvatarIconListItem):
    pass

class Item(OneLineAvatarListItem): #                                                            RENAME IT!!!!     TO DO!!!!
    source = StringProperty()

class CommandWithoutParameters(OneLineAvatarListItem):
    source = StringProperty()

class MineApp(MDApp):

    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Purple"
        self.theme_cls.accent_palette = "Yellow"

        self.all_bots = dict()

        self.all_commands = {
            'Connect Bot': {
                'ui_type': 'MDExpansionPanel',
                'icon': 'bot.jpg',
                'content': ConnectBotContent,
                'command': ConnectBotCommand,
                'command_parameters': {                 # Parameter: id
                    'username': 'nickname',
                    'ip': 'ip',
                    'port': 'port',
                },
                'function_str': 'self.all_bots[\'bot_name\'] = Bot'
            },
            'Move': {
                'ui_type': 'MDExpansionPanel',
	            'icon': 'move.png',
	            'content': MoveContent,
	            'command': CommandMove,
	            'command_parameters': {
                    'axis': 'axis',
                    'steps': 'steps'
                },
                'function_str': 'self.all_bots[\'bot_name\'].move'
            },
            'Chat': {
                'ui_type': 'MDExpansionPanel',
	            'icon': 'chat.png',
	            'content': ChatContent,
	            'command': CommandChat,
	            'command_parameters': {
                    'message': 'msg'
                },
                'function_str': 'self.all_bots[\'bot_name\'].write_message'
            },
            'Delay': {
                'ui_type': 'MDExpansionPanel',
	            'icon': 'delay.jpg',
	            'content': DelayContent,
	            'command': DelayCommand,
	            'command_parameters': {
                    'delay': 'delay'
                },
                'function_str': 'self.all_bots[\'bot_name\'].sleep'
            },
            'Place Block': {
                'ui_type': 'MDExpansionPanel',
	            'icon': 'grass_block.png',
	            'content': PlaceBlockContent,
	            'command': PlaceBlockCommand,
	            'command_parameters': {
                    'offset_x': 'place_offset_x',
                    'offset_y':'place_offset_y',
                    'offset_z': 'place_offset_z',
                    'blockface_str': 'place_blockface'
                },
                'function_str': 'self.all_bots[\'bot_name\'].place_block'
            },
            'Dig Block': {
                'ui_type': 'MDExpansionPanel',
                'icon': 'pickaxe.png',
                'content': DigBlockContent,
                'command': DigBlockCommand,
                'command_parameters': {
                    'offset_x': 'dig_offset_x',
                    'offset_y': 'dig_offset_y',
                    'offset_z': 'dig_offset_z',
                    'dig_time': 'dig_time',
                },
                'function_str': 'self.all_bots[\'bot_name\'].dig_block'
            },
            'For Loop Start': {
                'ui_type': 'MDExpansionPanel',
                'icon': 'loopstart.png',
                'content': ForLoopStartContent,
                'command': ForLoopStartCommand,
                'command_parameters': {
                    'iters': 'iters'
                },
                'function_str': None
            },
            'For Loop End': {
                'ui_type': 'Item',
                'icon': 'loopend.png',
                'content': None,
                'command': ForLoopEndCommand,
                'command_parameters': None,
                'function_str': None
            },
            'Use Current Item': {
                'ui_type': 'Item',
                'icon': 'use_item.png',
                'content': None,
                'command': UseCurrentItemCommand,
                'command_parameters': None,
                'function_str': 'self.all_bots[\'bot_name\'].use_current_item'
            },
        }

    # runs on start of the App
    def on_start(self):
        self.scripts = {}
        
        self.create_bot_cmmnd = MDExpansionPanel(icon='icons/bot.jpg',
                                           content=ConnectBotContent(),
                                           panel_cls=MDExpansionPanelOneLine(text="Connect Bot"))
        self.root.ids.list_cmmnds.add_widget(self.create_bot_cmmnd)

        # CREATING COMMAND-ADD POPUP
        self.popupcontent = PopupContent()

        for cmmnd in self.all_commands.keys():
            if cmmnd == "Connect Bot": continue
            icon_source = r'icons/{}'.format(self.all_commands[cmmnd]['icon'])
            self.cmmnd_item = Item(source=icon_source, text=cmmnd)
            self.popupcontent.ids.list_cmmnds_popup.add_widget(self.cmmnd_item)
        self.btn_cancel_command = MDFlatButton(text='Cancel')
        self.popup = MDDialog(title="Command Choosing", type='custom', buttons=[self.btn_cancel_command],
                              content_cls=self.popupcontent, auto_dismiss=False)
        self.btn_cancel_command.on_release = self.popup.dismiss

        # CREATING SAVE-SCRIPT POPUP
        self.savepopupcontent = SavePopupContent()
        self.btn_cancel_save = MDFlatButton(text="Cancel")
        self.savepopup = MDDialog(
            title='Saving Script',
            type='custom',
            buttons=[self.btn_cancel_save, MDRaisedButton(text='OK', on_release=self.save_script)],
            content_cls=self.savepopupcontent,
            auto_dismiss=False
        )
        self.btn_cancel_save.on_release = self.savepopup.dismiss

    # opening popup to choose command
    def cmmnd_popup(self):
        self.popup.open()

    # adding command
    def cmmnd_add(self, cmmnd):
        name = cmmnd.text

        if self.all_commands[name]['ui_type'] == 'MDExpansionPanel':
            cmmnd_to_add = MDExpansionPanel(
            								icon=cmmnd.source, 
            								panel_cls=MDExpansionPanelOneLine(text=cmmnd.text), 
            								content=self.all_commands[cmmnd.text]['content']()
            								)
        elif self.all_commands[name]['ui_type'] == "Item":
            cmmnd_to_add = CommandWithoutParameters(source=cmmnd.source, text=cmmnd.text)

        self.root.ids.list_cmmnds.add_widget(cmmnd_to_add)
        self.popup.dismiss()
    
    def close_save_popup(self, *args):
        self.savepopup.dismiss()

    def clear_script(self):
        self.root.ids.list_cmmnds.clear_widgets()
        self.root.ids.list_cmmnds.add_widget(self.create_bot_cmmnd)

    def save_popup(self):
        # Opening popup to save script
        self.savepopup.open()

    def save_script(self, button):
        name = self.savepopupcontent.ids['save_name'].text
        self.script = Script(text=name)
        self.script.cmmnds = []
        self.savepopup.dismiss()

        # TRANSLATING COMMANDS
        try:

            # Clearing from previous saving
            self.script.cmmnds = []

            for cmmnd_panel in self.root.ids.list_cmmnds.children:
                try:
                    if cmmnd_panel.text == "For Loop End": # TODO Make this work with any type of cmmnd in the same way, in the same statement
                        print("INFO: Here we have a For Loop End commmand.. line 262, minebot.py, .save_script()")
                        command_name = cmmnd_panel.text
                        if command_name == "For Loop End":
                            self.some_command = ForLoopEndCommand()
                        self.script.cmmnds.append(self.some_command)
                        continue
                    elif cmmnd_panel.text == "Use Current Item":
                        print("INFO: Here we have a Use Current Item commmand.. line 284, minebot.py, .save_script()")
                        command_name = cmmnd_panel.text
                        if command_name == "Use Current Item":
                            self.some_command = UseCurrentItemCommand()
                        self.script.cmmnds.append(self.some_command)
                        continue
                except AttributeError as e:
                    print(e, 'minebot.py , ln284')
                command_name = cmmnd_panel.panel_cls.text
                self.some_command = self.all_commands[command_name]['command']()
                for parameter_str in self.all_commands[command_name]['command_parameters'].keys():
                    try:
                        parameter_id = self.all_commands[command_name]['command_parameters'][parameter_str]
                        exec(f'parameter_value = cmmnd_panel.content.ids.{parameter_id}.text')
                        exec('parameter_value = json.dumps(parameter_value)') # Converts in this way: 'This sentence has some "quotes" in it\n'  --->  '"This sentence has some \\"quotes\\" in it\\n"'
                        exec('self.parameter_value = parameter_value')
                        exec('print(self.parameter_value, parameter_value, "ln271, minebot.py")')
                    except AttributeError as e:
                        exec('self.parameter_value = cmmnd_panel.content.ids.%s.active' % (self.all_commands[command_name]['command_parameters'][parameter_str]))
                    
                    # SPECIALIAZING   #TODO MAKE IT WITHIN THE COMMANDS, so they take care of it
                    if parameter_str == 'port' or parameter_str == 'delay' or parameter_str == 'steps' or parameter_str == "iters":
                        try:
                            exec(f'self.some_command.{parameter_str} = int({self.parameter_value})')
                        except ValueError:
                            exec(f'self.some_command.{parameter_str} = float({self.parameter_value})')
                    else:
                        exec(f'self.some_command.{parameter_str} = {self.parameter_value}')

                self.script.cmmnds.append(self.some_command)

            self.root.ids.list_scripts.add_widget(self.script)
            self.script.cmmnds.reverse()

            #Setting indexes
            for k in range(len(self.script.cmmnds)):
                self.script.cmmnds[k].index = k

            self.scripts[name] = self.script.cmmnds

        except ValueError as e:
            print('WARNING', e)
            raise_error_popup('Please, check if all the command data is correct.')

    def play_script_with_threading(self, script):
        """Making scripts work in parallel"""
        threading.Timer(0, lambda script: self.play_script(script), [script]).start()

    def play_script(self, script):
        # Running commands
        script_name = script.text
        bot_name = self.scripts[script_name][0].username # 0 - index of the Connect Bot command

        try:
            for cmmnd in self.scripts[script_name]:
                try:
                    if cmmnd.name == 'Connect Bot' and self.all_bots[bot_name].connection.connected: continue
                except KeyError as e:
                    print(e, '249 line, play_script. NO BOT WITH SUCH NAME IN self.all_bots')
                if cmmnd.name == "For Loop Start":
                    self.uncover_for_loop(script_name, cmmnd, bot_name)
                elif cmmnd.name == "For Loop End": continue
                else:
                    print(cmmnd, 'ln338 minebot.py')
                    exec(self.all_commands[cmmnd.name]['function_str'].replace('bot_name', bot_name)+"(cmmnd)")

                time.sleep(COMMANDS_DELAY)

        except ValueError as e:
            print('WARNING', e)
            raise_error_popup('Please, check if all the command data is correct.')

        except socket.gaierror as e:
            print('WARNING', e)
            raise_error_popup('Check if all the connection data is correct.')

    def uncover_for_loop(self, script_name, start_loop_command, bot_name):                                                         # TO DO!!! Add an "index" parameter for command classes. So you can check their pos in script # TO-DO 2. Make it work with only For_loop_start instance given
        print('entered')
        iters = start_loop_command.iters
        script = self.scripts[script_name]

        first_command_index = start_loop_command.index + 1
        for command in script[first_command_index:]:
            if command.name == "For Loop End":
                loop_end = command.index
                break

        loop_commands = script[first_command_index : loop_end] # FIGURE OUT WHY YOU NEED TO -1 LOOP_START_INDEX
        commands_to_insert = loop_commands * iters

        insertion_end = loop_end + len(commands_to_insert) -1

        j = 0
        for index in range(loop_end, insertion_end):
            j += 1
            script.insert(index, commands_to_insert[j])

def raise_error_popup(text):
    button_ok = MDRaisedButton(text="OK")
    info_popup = MDDialog(title='ERROR', text=text, auto_dismiss=False, type='custom', buttons=[button_ok])
    info_popup.buttons[0].on_release = info_popup.dismiss
    info_popup.open()

if __name__ == "__main__":
    app = MineApp()
    app.run()