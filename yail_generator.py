import json
from Text2App import Text2App

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
	CA = '<|comp_actions|>'
	CM = '<|comp_method|>'
	CAA = '<|comp_action_arg|>'
	CAAT = '<|comp_action_arg_type|>'

class EventComponentNames:
	BUTTON = 'Button'
	SWITCH = 'Switch'
	ACCELEROMETERSENSOR = 'AccelerometerSensor'

class Events:
	BUTTON_CLICK_SAR = f'{Tags.CN_L}clicked'
	SWITCH_CHANGED_SAR = f'{Tags.CN_L}flipped'
	ACCELEROMETER_SHAKING_SAR = f'{Tags.CN_L}shaken'
	BUTTON_CLICK_YAIL = 'Clicked'
	SWITCH_CHANGED_YAIL = 'Changed'
	ACCELEROMETER_SHAKING_YAIL = 'Shaking'

class YailGenerator:

	def __init__(self, username, project_name, vis_components_scm) -> None:
		self.app_name = project_name
		self.package_name = f'ai_{username}'
		self.screen_id = 1

		self.vis_components_scm = vis_components_scm
		
		self.code_tokens = []

		self.yail = list()
	
		class YailTemplates:
			INIT = '|#\!\n$Source $Yail\n\!#'
			DEFINE_FORM = f'(define-form appinventor.{self.package_name}.{self.app_name}.Screen{self.screen_id} Screen{self.screen_id} #t)\n(require <com.google.youngandroid.runtime>)\n'

			COMP_PKG = 'com.google.appinventor.components.runtime'

			# Yail Templates
			DO_AFTER_FORM_CREATION = f';;; Screen{self.screen_id}\n\n(do-after-form-creation (set-and-coerce-property! \'Screen{self.screen_id} \'AppName \"{self.app_name}\" \'text)\n\
	(set-and-coerce-property! \'Screen{self.screen_id} \'Scrollable #t \'boolean)\n\
	(set-and-coerce-property! \'Screen{self.screen_id} \'ShowListsAsJson #t \'boolean)\n\
	(set-and-coerce-property! \'Screen{self.screen_id} \'Sizing \"Responsive\" \'text)\n\
	(set-and-coerce-property! \'Screen{self.screen_id} \'Title \"Screen1\" \'text)\n\
	)'
			_ADD_COMP = f'(add-component Screen{self.screen_id} {COMP_PKG}.{Tags.CT} {Tags.CN}\n{Tags.SCP})\n'
			ADD_COMP = f";;; {Tags.CN}\n\n{_ADD_COMP}\n"

			SET_AND_COERCE_PROPERTY = f'(set-and-coerce-property! \'{Tags.CN} \'{Tags.CP} \'{Tags.CPV} \'{Tags.CPT})\n'
			COMPTYPE_TEXT = 'text'
			COMPTYPE_BOOL = 'boolean'

			DEFINE_EVENT = f'(define-event {Tags.CN} {Tags.EN}()(set-this-form)\n\t{Tags.CA}\n)'
			CALL_COMPONENT_METHOD = f'(call-component-method \'{Tags.CN} \'{Tags.CM} (*list-for-runtime*{Tags.CAA}) \'({Tags.CAAT}))\n'
			INIT_RUNTIME = '(init-runtime)'

		self.T = YailTemplates()


	def has_events(self, comp_type: str):
		if comp_type in [EventComponentNames.BUTTON, EventComponentNames.SWITCH, EventComponentNames.ACCELEROMETERSENSOR]:
			return True
		return False

	def _get_component_event(self, comp_type: str, comp_name: str) -> tuple[str, str]:
		if comp_type == EventComponentNames.BUTTON:
			return Events.BUTTON_CLICK_YAIL, Events.BUTTON_CLICK_SAR.replace(Tags.CN_L, comp_name.lower())
		elif comp_type == EventComponentNames.SWITCH:
			return Events.SWITCH_CHANGED_YAIL, Events.SWITCH_CHANGED_SAR.replace(Tags.CN_L, comp_name.lower())
		elif comp_type == EventComponentNames.ACCELEROMETERSENSOR:
			comp_name_lower = f'accelerometer{comp_name[-1]}'
			# note SAR token is <accelerometer\dshaken> but component name is AcclerometerSensor\d
			return Events.ACCELEROMETER_SHAKING_YAIL, Events.ACCELEROMETER_SHAKING_SAR.replace(Tags.CN_L, comp_name_lower)

	def _get_component_property_type(self, comp_type: str) -> str:
		
		bool_properties = ['Enabled']
		
		if comp_type in bool_properties:
			return self.T.COMPTYPE_BOOL
		return self.T.COMPTYPE_TEXT
	

	def generate(self):

		print('\n\nYAIL-GENERATOR::\n')

		self.yail.append(self.T.INIT)
		self.yail.append(self.T.DEFINE_FORM)
		self.yail.append(self.T.DO_AFTER_FORM_CREATION)

		print('SAR', self.code_tokens)

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
					scp = self.T.SET_AND_COERCE_PROPERTY.replace(Tags.CP, k).replace(Tags.CPV, v).replace(Tags.CPT, self._get_component_property_type(k))
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
				print('Event', define_event)
				call_comps = ''
				for i in range(event_start_idx + 1, event_end_idx):
					token = self.code_tokens[i]
					if token.startswith('<player'):
						argument_idx = i + 1
						comp_name = f'Player{token[-2:-1]}'
						argument = 'start' if 'Start' in self.code_tokens[argument_idx] else 'Stop'
						i += 3
						call_comp_method = self.T.CALL_COMPONENT_METHOD.replace(Tags.CM, argument).replace(Tags.CAA, '').replace(Tags.CAAT, '').replace(Tags.CN, comp_name)
						call_comps += call_comp_method
					if token.startswith('<video_player'):
						argument_idx = i + 1
						comp_name = f'VideoPlayer{token[-2:-1]}'
						argument = 'start' if 'Start' in self.code_tokens[argument_idx] else 'Stop'
						call_comp_method = self.T.CALL_COMPONENT_METHOD.replace(Tags.CM, argument).replace(Tags.CAA, '').replace(Tags.CAAT, '').replace(Tags.CN, comp_name)
						i += 3
						call_comps += call_comp_method
						print(call_comp_method)
				self.yail.append(define_event.replace(Tags.CA, call_comps))
			except ValueError as e:
				print('Error:', e)
				continue

			

		self.yail.append(self.T.INIT_RUNTIME)
		self._write_file()

	def _write_file(self):
		f = open(f'Screen{self.screen_id}.yail', 'a')
		for item in self.yail:
			f.write(item)
			f.write('\n')
		f.close()


	
if __name__ == '__main__':
	from Text2App import Text2App, sar_to_aia

	NL = "make it having two buttons , a time picker , a switch , and a video player. when the switch is pressed, pause the video ."
	t2a = Text2App(NL, nlu='roberta')
	sar_to_aia(t2a, project_name="SpeakIt")    
