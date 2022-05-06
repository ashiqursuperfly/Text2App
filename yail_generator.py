import json
from Text2App import Text2App

"""
Questions to Mehrab bhai:
1. Set Label Action
2.
"""

class SCMKeys:
	NAME = '$Name'
	TYPE = '$Type'
	VERSION = '$Version'
	UUID = 'Uuid'

class Tags:
	CT = '<|comp_type|>'
	CN = '<|comp_name|>'
	CN_L = '<|comp_name_lowercase|>'
	CP = '<|comp_prop|>'
	CPV = '<|comp_prop_value|>'
	CPT = '<|comp_prop_type|>'
	SCP = '<|set_and_coerce_property|>'
	EN = '<|event_name|>'
	EV = '<|event_value|>'
	CA = '<|comp_actions|>'
	CM = '<|comp_method|>'
	CAA = '<|comp_action_arg|>'
	CAAT = '<|comp_action_arg_type|>'

class EventComponentNames:
	BUTTON = 'Button'
	SWITCH = 'Switch'
	ACCELEROMETERSENSOR = 'AccelerometerSensor'
	CAMERA = 'Camera'

class Events:
	BUTTON_CLICK_SAR = f'{Tags.CN_L}clicked'
	SWITCH_CHANGED_SAR = f'{Tags.CN_L}flipped'
	ACCELEROMETER_SHAKING_SAR = f'{Tags.CN_L}shaken'
	AFTER_PICTURE_SAR = f'{Tags.CN_L}afterpicture'
	BUTTON_CLICK_YAIL = 'Clicked'
	SWITCH_CHANGED_YAIL = 'Changed'
	ACCELEROMETER_SHAKING_YAIL = 'Shaking'
	AFTER_PICTURE_YAIL = 'AfterPicture'

class CompMethods:
	START = 'Start'
	STOP = 'Stop'
	SPEAK = 'Speak'
	TAKE_PICTURE = 'TakePicture'

class YailGenerator:

	def __init__(self, username, project_name, vis_components_scm, texts_dict) -> None:

		print('\n\nYAIL-GENERATOR::\n')

		print('Texts', texts_dict)

		self.app_name = project_name
		self.package_name = f'ai_{username}'
		self.screen_id = 1

		self.vis_components_scm = vis_components_scm
		
		self.code_tokens = []

		self.yail = list()
	
		class YailTemplates:
			INIT = '#|\n$Source $Yail\n|#'
			DEFINE_FORM = f'(define-form appinventor.{self.package_name}.{self.app_name}.Screen{self.screen_id} Screen{self.screen_id} #t)\n(require <com.google.youngandroid.runtime>)\n'

			COMP_PKG = 'com.google.appinventor.components.runtime'

			# Yail Templates
			DO_AFTER_FORM_CREATION = f';;; Screen{self.screen_id}\n\n(do-after-form-creation (set-and-coerce-property! \'Screen{self.screen_id} \'AppName \"{self.app_name}\" \'text)\n\
	(set-and-coerce-property! \'Screen{self.screen_id} \'Scrollable #t \'boolean)\n\
	(set-and-coerce-property! \'Screen{self.screen_id} \'ShowListsAsJson #t \'boolean)\n\
	(set-and-coerce-property! \'Screen{self.screen_id} \'Sizing \"Responsive\" \'text)\n\
	(set-and-coerce-property! \'Screen{self.screen_id} \'Title \"Screen1\" \'text)\n\
	)\n'
			_ADD_COMP = f'(add-component Screen{self.screen_id} {COMP_PKG}.{Tags.CT} {Tags.CN}\n{Tags.SCP})'
			ADD_COMP = f";;; {Tags.CN}\n\n{_ADD_COMP}\n"

			SET_AND_COERCE_PROPERTY = f'(set-and-coerce-property! \'{Tags.CN} \'{Tags.CP} {Tags.CPV} \'{Tags.CPT})\n'
			COMPTYPE_TEXT = 'text'
			COMPTYPE_BOOL = 'boolean'

			DEFINE_EVENT = f'(define-event {Tags.CN} {Tags.EN}({Tags.EV})(set-this-form)\n\t{Tags.CA})'
			CALL_COMPONENT_METHOD = f'(call-component-method \'{Tags.CN} \'{Tags.CM} (*list-for-runtime*{Tags.CAA}) \'({Tags.CAAT}))\n'

			READ_FORMATTED_TIME = f'(call-yail-primitive string-append (*list-for-runtime* (get-property \'{Tags.CN} \'Hour) (call-yail-primitive string-append (*list-for-runtime* \"hours\" (call-yail-primitive string-append (*list-for-runtime* (get-property \'{Tags.CN} \'Minute) \"minutes\" ) \'(text text ) \"join\") ) \'(text text ) \"join\") ) \'(text text ) \"join\")'
		

			INIT_RUNTIME = '(init-runtime)'

		self.T = YailTemplates()


	def has_events(self, comp_type: str):
		if comp_type in [EventComponentNames.BUTTON, EventComponentNames.SWITCH, EventComponentNames.ACCELEROMETERSENSOR, EventComponentNames.CAMERA]:
			return True
		return False

	def _get_argument_value(self, argument: str):
		if argument.startswith("<textboxtext"):
			id = argument[-2:-1]
			return f'(get-property \'TextBox{id} \'Text)'
		elif argument.startswith("<time"):
			id = argument[-2:-1]
			comp_name = f'TimePicker{id}'
			return self.T.READ_FORMATTED_TIME.replace(Tags.CN, comp_name)
		elif argument.startswith("<date"):
			id = argument[-2:-1]
			return "TODO"
		else:
			return f'\"{argument}\"'



	def _get_component_event(self, comp_type: str, comp_name: str) -> tuple[str, str]:
		if comp_type == EventComponentNames.BUTTON:
			return Events.BUTTON_CLICK_YAIL, Events.BUTTON_CLICK_SAR.replace(Tags.CN_L, comp_name.lower())
		elif comp_type == EventComponentNames.SWITCH:
			return Events.SWITCH_CHANGED_YAIL, Events.SWITCH_CHANGED_SAR.replace(Tags.CN_L, comp_name.lower())
		elif comp_type == EventComponentNames.ACCELEROMETERSENSOR:
			comp_name_lower = f'accelerometer{comp_name[-1]}'
			# note SAR token is <accelerometer\dshaken> but component name is AcclerometerSensor\d
			return Events.ACCELEROMETER_SHAKING_YAIL, Events.ACCELEROMETER_SHAKING_SAR.replace(Tags.CN_L, comp_name_lower)
		elif comp_type == EventComponentNames.CAMERA:
			comp_name_lower = f'camera{comp_name[-1]}'
			return Events.AFTER_PICTURE_YAIL, Events.AFTER_PICTURE_SAR.replace(Tags.CN_L, comp_name_lower)

	def _get_component_property_type(self, comp_type: str) -> str:
		
		bool_properties = ['Enabled']
		
		if comp_type in bool_properties:
			return self.T.COMPTYPE_BOOL
		return self.T.COMPTYPE_TEXT
	
	def inject_additional_code_tokens(self):
		initial_len = len(self.code_tokens)
		for idx in range(initial_len):
			token = self.code_tokens[idx]
			if token == '<capture_and_show>':
				action = self.code_tokens[idx-1]
				id = action[-2:-1]
				comp_name = f'Camera{id}'	
				l = len(self.code_tokens)
				self.code_tokens.insert(l-1, f'<{Events.AFTER_PICTURE_SAR.replace(Tags.CN_L, comp_name.lower())}>')
				self.code_tokens.insert(l, f'<show_picture{id}>')
				self.code_tokens.insert(l+1, f'<Image{id}>')
				self.code_tokens.insert(l+2, f'</show_picture{id}>')
				self.code_tokens.insert(l+3, f'</{Events.AFTER_PICTURE_SAR.replace(Tags.CN_L, comp_name.lower())}>')							
				
		print('SAR', self.code_tokens)

	def generate(self):

		self.yail.append(self.T.INIT)
		self.yail.append(self.T.DEFINE_FORM)
		self.yail.append(self.T.DO_AFTER_FORM_CREATION)

		self.inject_additional_code_tokens()
		
		for component in self.vis_components_scm:
			j = json.loads(component)
			name = j[SCMKeys.NAME]
			type = j[SCMKeys.TYPE]
			version = j[SCMKeys.VERSION]
			uuid = j[SCMKeys.UUID]
			properties = {key: j[key] for key in j if key not in [SCMKeys.NAME, SCMKeys.TYPE, SCMKeys.VERSION, SCMKeys.UUID]}
			print('Type: ', type, 'Name:', name)

			scps = ''
			if properties:
				print('Properties:')
				for k, v in properties.items():
					scp = self.T.SET_AND_COERCE_PROPERTY.replace(Tags.CP, k).replace(Tags.CPV, f'\"{v}\"').replace(Tags.CPT, self._get_component_property_type(k))
					scps += scp
					
			add_comp = self.T.ADD_COMP.replace(Tags.SCP, scps).replace(Tags.CN, name).replace(Tags.CT, type)
			self.yail.append(add_comp)

			if not self.has_events(type):
				continue

			event_name, sar_token = self._get_component_event(type, name)

			sar_token_start = f'<{sar_token}>'
			sar_token_end = f'</{sar_token}>'

			try:
				event_start_idx = self.code_tokens.index(sar_token_start)
				event_end_idx = self.code_tokens.index(sar_token_end)
			
				define_event = self.T.DEFINE_EVENT.replace(Tags.EN, event_name).replace(Tags.CN, name)
				# print('Event', define_event)
				call_comps = ''
				for i in range(event_start_idx + 1, event_end_idx):
					action = self.code_tokens[i]
					if action.startswith('<player'):
						argument_idx = i + 1
						comp_name = f'Player{action[-2:-1]}'
						argument = CompMethods.START if 'start' in self.code_tokens[argument_idx] else CompMethods.STOP
						i += 3
						call_comp_method = self.T.CALL_COMPONENT_METHOD.replace(Tags.CM, argument).replace(Tags.CAA, '').replace(Tags.CAAT, '').replace(Tags.CN, comp_name)
						call_comps += call_comp_method
						define_event = define_event.replace(Tags.EV, '')
					
					if action.startswith('<video_player'):
						argument_idx = i + 1
						comp_name = f'VideoPlayer{action[-2:-1]}'
						argument = CompMethods.START if 'start' in self.code_tokens[argument_idx] else CompMethods.STOP
						call_comp_method = self.T.CALL_COMPONENT_METHOD.replace(Tags.CM, argument).replace(Tags.CAA, '').replace(Tags.CAAT, '').replace(Tags.CN, comp_name)
						i += 3
						call_comps += call_comp_method
						define_event = define_event.replace(Tags.EV, '')
					
					if action.startswith('<label'):
						comp_name = f'Label{action[-2:-1]}'
						argument = self.code_tokens[i + 1]
						argument_val = self._get_argument_value(argument)
						set_property = self.T.SET_AND_COERCE_PROPERTY.replace(Tags.CN, comp_name).replace(Tags.CP, 'Text').replace(Tags.CPV, argument_val).replace(Tags.CPT, self._get_component_property_type('Text'))
						i += 3
						call_comps += set_property
						define_event = define_event.replace(Tags.EV, '')
					
					if action.startswith('<text2speech'):
						comp_name = f'TextToSpeech{action[-2:-1]}'
						argument = self.code_tokens[i + 1]
						argument_val = self._get_argument_value(argument)
						method = CompMethods.SPEAK
						call_comp_method = self.T.CALL_COMPONENT_METHOD.replace(Tags.CM, method).replace(Tags.CAA, f' {argument_val}').replace(Tags.CAAT, 'text').replace(Tags.CN, comp_name)
						i += 3
						call_comps += call_comp_method
						define_event = define_event.replace(Tags.EV, '')
					
					if action.startswith('<camera'):
						id = action[-2:-1]
						comp_name = f'Camera{id}'
						argument = self.code_tokens[i + 1]
						method = CompMethods.TAKE_PICTURE
						call_comp_method = self.T.CALL_COMPONENT_METHOD.replace(Tags.CM, method).replace(Tags.CAA, '').replace(Tags.CAAT, '').replace(Tags.CN, comp_name)
						i += 3
						call_comps += call_comp_method
						define_event = define_event.replace(Tags.EV, '')

					if action.startswith('<show_picture'):
						comp_name = f'Camera{action[-2:-1]}'
						argument = self.code_tokens[i + 1]
						argument = argument[1: len(argument)-1] # e.g: <ImageX>
						set_property = self.T.SET_AND_COERCE_PROPERTY.replace(Tags.CN, argument).replace(Tags.CP, 'Picture').replace(Tags.CPV, '(lexical-value $image)').replace(Tags.CPT, self._get_component_property_type('Picture'))
						i += 3
						define_event = define_event.replace(Tags.EV, '$image')
						call_comps += set_property

				self.yail.append(define_event.replace(Tags.CA, call_comps))
			except ValueError as e:
				print('Error:', e)
				continue

		self.yail.append(self.T.INIT_RUNTIME)

	def yail_string(self):
		res = str()
		for item in self.yail:
			res += item
			res += '\n'
		return res


	
if __name__ == '__main__':
	from Text2App import Text2App, sar_to_aia

	NL = "make it having a button, a label and a timepicker. when the button is pressed, set label to time."
	# NL = "create mobile application that has a camera and a button"
	# NL = "make mobile application include a label containing a motion sensor , a switch , a camera , a tool box , a button , an audio with a random music , a label , random time picker , and a video with source string0 . when the motion sensor is shaken, set a label up to time . when the switch is pressed, pause video . if the button was pressed, set the label text to string1"
	t2a = Text2App(NL, nlu='roberta')
	sar_to_aia(t2a, project_name="LabelBtnTime")    
