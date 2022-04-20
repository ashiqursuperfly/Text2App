class YailGenerator:
    
    def __init__(self, package_name, app_name) -> None:
        self.yail = list()
        self.screen_name = 'Screen1'
        self.templates = {
            'init': '|#\!\n$Source $Yail\n\!#',
            'define-form': f'(define-form appinventor.{package_name}.{app_name}.{self.screen_name} {self.screen_name} #t)\n(require <com.google.youngandroid.runtime>)',
            'do-after-form-creation': f'(do-after-form-creation (set-and-coerce-property! \'{self.screen_name} \'AppName \"{app_name}\" \'text)\n\
 (set-and-coerce-property! \'{self.screen_name} \'Scrollable #t \'boolean)\n\
 (set-and-coerce-property! \'{self.screen_name} \'ShowListsAsJson #t \'boolean)\n\
 (set-and-coerce-property! \'{self.screen_name} \'Sizing \"Responsive\" \'text)\n\
 (set-and-coerce-property! \'{self.screen_name} \'Title \"Screen1\" \'text)\n\
)',
        }

        
    def generate(self):
        self.yail.append(self.templates['init'])
        self.yail.append(self.templates['define-form'])
        self.yail.append(self.templates['do-after-form-creation'])
        self._write_file()

    def _write_file(self):
        f = open(f'{self.screen_name}.yail', 'a')
        for item in self.yail:
            f.write(item)
            f.write('\n')
        f.close()


if __name__ == '__main__':
    g = YailGenerator('ai_anonymuser', 'yailtestapp')
    g.generate()
