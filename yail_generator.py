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
    CP = '<|comp_prop|>'
    CPV = '<|comp_prop_value|>'
    CPT = '<|comp_prop_type|>'
    SCP = '<|set_and_coerce_property|>'

class YailGenerator:

    def __init__(self, username, project_name, vis_components_scm) -> None:


        self.app_name = project_name
        self.package_name = f'ai_{username}'
        self.screen_id = 1

        self.vis_components_scm = vis_components_scm
        # self.code_tokens = tokens[tokens.index("<code>"):tokens.index("</code>")+1] if "<code>" in tokens else None

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
        
        self.T = YailTemplates()

    def get_component_property_type(self, comp_type: str) -> str:
        
        bool_properties = ['Enabled']
        
        if comp_type in bool_properties:
            return self.T.COMPTYPE_BOOL
        return self.T.COMPTYPE_TEXT
        

    def generate(self):

        print('\n\nYAIL-GENERATOR::\n')

        self.yail.append(self.T.INIT)
        self.yail.append(self.T.DEFINE_FORM)
        self.yail.append(self.T.DO_AFTER_FORM_CREATION)

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
                    scp = self.T.SET_AND_COERCE_PROPERTY.replace(Tags.CP, k).replace(Tags.CPV, v).replace(Tags.CPT, self.get_component_property_type(k))
                    scps += scp
                    
            add_comp = self.T.ADD_COMP.replace(Tags.SCP, scps).replace(Tags.CN, name).replace(Tags.CT, type)
            self.yail.append(add_comp)

            
        
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


