

def smb_strip_comments(self, auxparam_in):
        parsed_config = ""
        for entry in auxparam_in.splitlines():
            if entry == "" or entry.startswith(('#', ';')):
                continue
            parsed_config += entry if len(parsed_config) == 0 else f'\n{entry}'

        return parsed_entry

