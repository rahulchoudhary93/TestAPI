import requests
import json
import os
import re
import random
import string
import xlrd
import configparser


class TESTAPI(object):
    def __init__(self, template_path, datarow, **kwargs):

        urlkey = "${URL}"
        headerkey = "${HEADER}"
        requestkey = "${REQUEST}"
        methodkey = "${METHOD}"
        self.template_path = template_path
        self.template_file_name = os.path.splitext(os.path.basename(template_path))[0]
        print(self.template_file_name)
        self.datarow = datarow

        with open(self.template_path, 'rt') as template:
            self.template_content = json.load(template)
            print(self.template_content)

        self.url = self.template_content[urlkey]
        print("URL:", self.url)
        self.headers = self.template_content[headerkey]
        print("Headers:", self.headers)
        self.request = self.template_content[requestkey]
        print("Request:", self.request)
        self.method = self.template_content[methodkey]
        print("Method:", self.method)

        self.variable_list = {}
        self.returned_params = {}

        self.data_wb = xlrd.open_workbook(os.path.join(os.path.curdir, 'apidata/{}.xlsx'.format(self.template_file_name)))

    def _get_req_var(self, var_name):
        try:
            var = self.returned_params[var_name]
        except Exception as e:
            var = None
            print("Variable not found in the returned parameters.", e)
        try:
            config = configparser.RawConfigParser()
            config.read('config.ini')
            var = config['CONFIGPARAMS'][var_name]
        except Exception as e:
            var = None
            print("Variable not found in config file.", e)

        if var == None:
            try:
                configG = configparser.RawConfigParser()
                configG.read('global.var')
                var = configG['CONFIGPARAMS'][var_name]
            except Exception as e:
                var = None
                print("Variable not found in Global Variables.", e)

        if var == None:
            try:
                request_sheet = self.data_wb.sheet_by_name('request')
                for i, j in enumerate(request_sheet.row_values(0)):
                    if var_name == j:
                        val = request_sheet.cell_value(self.datarow, i)
                        var = val
                        break
            except Exception as e:
                var = None
                print("Request variables not found in the request data file.", e)
        if var == None:
            raise Exception("Undeclared Variable found - ", var_name)

        return var

    def _update_var_as_global(self, var, val):
        configG = configparser.RawConfigParser()
        configG.read('global.var')
        configG.set('GLOBAL VARIABLES', var, val)

        with open('global.var', 'w') as configfile:
            configG.write(configfile)
            print("The global file {} has been updated.".format('global.var'))

    def _generate_random_string(self, var_split, type_index, length_index):
        if var_split[type_index] == 'C':
            letters = string.ascii_uppercase
        elif var_split[type_index] == 'N':
            letters = string.digits
        elif var_split[type_index] == 'A':
            letters = string.digits + string.ascii_uppercase
        else:
            letters = string.ascii_lowercase
        autogenerated_val = ''.join(random.choice(letters) for i in range(int(var_split[length_index])))
        variable_name = var_split[-1]
        return variable_name, autogenerated_val

    def _resolve_variables(self, autogenerated_vars):
        for var in autogenerated_vars:
            var_split = var[2:-1].split(';')
            if len(var_split) == 5 or len(var_split) == 4:
                key, autogenerated_val = self._generate_random_string(var_split, -3, -2)
                self.variable_list[key] = autogenerated_val
                if var_split[0] == 'RETURN':
                    self.returned_params[key] = autogenerated_val
            elif len(var_split) == 2:
                if var_split[0] == 'VAR':
                    self.variable_list[var_split[1]] = self._get_req_var(var_split[1])
            elif len(var_split) == 3:
                if var_split[0] == 'RETURN' and var_split[1] == 'VAR':
                    var_val = self._get_req_var(var_split[-1])
                    self.variable_list[var_split[-1]] = var_val
                    self.returned_params[var_split[-1]] = var_val

    def _validate_response(self, response):
        try:
            response_sheet = self.data_wb.sheet_by_name('response')
            available_vars = {}
            for i, j in enumerate(response_sheet.row_values(self.datarow)):
                if j != "":
                    res_var = response_sheet.cell_value(0, i)
                    available_vars[res_var] = j
        except Exception as e:
            var = None
            print("Request variables not found in the request data file.", e)

        for key, val in available_vars.items():
            match = re.findall('\${VAR;.*?\}', str(val))
            returned = re.findall('\${RETURNG;VAR;.*?\}', str(val))
            if match != []:
                var_name = match[0][2:-1].split(';')[-1]
                if var_name in self.returned_params.keys():
                    pattern = '\"{}.*?\"{}"'.format(key, self.returned_params[var_name])
                    found_in_res = re.findall(pattern, response)
                if found_in_res == []:
                    raise Exception("Test Failed! Expected value {} not found for {}.".format(self.returned_params[var_name], key))
            elif returned != []:
                var_name = returned[0][2:-1].split(';')[-1]
                to_be_validated_flag = returned[0][2:-1].split(';')[1]
                if to_be_validated_flag == 'VAR':
                    if var_name in self.returned_params.keys():
                        pattern = '\"{}.*?\"{}"'.format(key, self.returned_params[var_name])
                        found_in_res = re.findall(pattern, response)
                    if found_in_res == []:
                        raise Exception(
                            "Test Failed! Expected value {} not found for {}.".format(self.returned_params[var_name], key))
                    else:
                        global_val = found_in_res[0].split(':')[-1]
                        self._update_var_as_global(key, global_val)
                else:
                    global_val = found_in_res[0].split(':')[-1]
                    self._update_var_as_global(key, global_val)
            else:
                pattern = '\"{}.*?\"{}"'.format(key, val)
                found_in_res = re.findall(pattern, response)
                if found_in_res == []:
                    raise Exception("Test Failed! Expected value {} not found for {}.".format(val, key))




    def run_template(self):
        request_vars = re.findall('\${RETURN;.*?\}|\${AUTOGENERATE;.*?\}|\${VAR;.*?\}', str(self.request))
        print("Variables in the template: ", request_vars)
        self._resolve_variables(request_vars)
        print("Resolved Variables: ", self.variable_list)

        url_vars = re.findall('\${RETURN;.*?\}|\${AUTOGENERATE;.*?\}|\${VAR;.*?\}', str(self.url))
        print("URL Variables: ", url_vars)
        self._resolve_variables(url_vars)

        header_vars = re.findall('\${RETURN;.*?\}|\${AUTOGENERATE;.*?\}|\${VAR;.*?\}', str(self.headers))
        print("Header Variables: ", header_vars)
        self._resolve_variables(header_vars)

        req_string = str(self.request)
        url_string = str(self.url)
        header_string = str(self.headers)

        for key, val in self.variable_list.items():
            for req_tags in request_vars:
                    if key in req_tags:
                        req_string = req_string.replace(req_tags, val)

            for url_tags in url_vars:
                    if key in url_tags:
                        url_string = url_string.replace(url_tags, val)

            for header_tags in header_vars:
                    if key in header_tags:
                        header_string = header_string.replace(header_tags, val)

        header_string = header_string.replace('\'', '\"')
        req_string = req_string.replace('\'', '\"')
        if header_string != "":
            updated_header = json.loads(header_string)
        else:
            updated_header = ""
        if req_string != "":
            updated_request = json.loads(req_string)
        else:
            updated_request = ""

        print(url_string, "\n", updated_header, "\n", updated_request)
        if self.method == "POST":
            resp = requests.post(url_string, headers=updated_header, json=updated_request)
        elif self.method == "GET":
            resp = requests.get(url_string, headers=updated_header, json=updated_request)
        elif self.method == "PUT":
            resp = requests.put(url_string, headers=updated_header, json=updated_request)
        elif self.method == "DELETE":
            resp = requests.delete(url_string, headers=updated_header, json=updated_request)
        else:
            return "Method not supported"
        print(resp.status_code, resp)
        if resp.status_code in (200, 201):
            responsejson = json.dumps(resp.json())
            self._validate_response(responsejson)
            return responsejson
        else:
            raise Exception("API failed with status code: {}".format(resp.status_code))

def testrest():
    templates = os.listdir(os.path.join(os.path.curdir, 'template'))
    print(templates)
    for file in templates:
        template_path = os.path.join(os.path.curdir, 'template/{}'.format(file))
        print(template_path)
        data_wb = xlrd.open_workbook(
            os.path.join(os.path.curdir, 'apidata/{}.xlsx'.format(os.path.splitext(os.path.basename(file))[0])))
        total_rows = data_wb.sheet_by_name('request').nrows
        print(total_rows)
        for datarow in range(1, total_rows):
            try:
                test = TESTAPI(template_path, datarow)
                response = test.run_template()
                print(response)
            except Exception as e:
                print("Test Failed for datarow {}. ".format(datarow), e)


if __name__ == '__main__':
    testrest()

