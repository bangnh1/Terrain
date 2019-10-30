#!/usr/bin/env python3

class filterParameter:

    def __init__(self):
        self.newData = {}
        self.arrayParameter = []

    def filterKeyValueParameter(self, data):

        for key, value in data.items():
            if "." not in key and value != '':
                self.newData[key] = value

        return self.newData


    def filterArrayParameter(self, data):

        for key, value in data.items():
            if "." in key and "#" not in key and "tags" not in key and int(len(key.split("."))) == 2:
                self.arrayParameter.append(key.split(".")[0])

        arrayParameterSet = set(self.arrayParameter)

        for parameter in arrayParameterSet:
            newList = []
            for key, value in data.items():
                if "#" not in key and parameter in key and value != '':
                    newList.append(value)
            self.newData[parameter.split('.')[0]] = newList

        return self.newData

    ## Special thanks to hung_pt for this function
    def filterMappingParameter(self, data):

        def isValid(key):
            if '.' in key and 'tags' not in key and '#' not in key:
                return True
            else:
                return False

        def processAllLevel(keys, value, data, repeat=0, isLastArr=False):
            if repeat == len(keys) - 1:
                if isLastArr != True:
                    return data.update({keys[repeat]: value})
                else:
                    return data.append(value)
            else:
                if repeat + 1 == len(keys) - 1:
                    try:
                        int(keys[repeat+1])
                        data.setdefault(keys[repeat], [])
                        isLastArr = True
                    except:
                        data.setdefault(keys[repeat], {})
                else:
                    data.setdefault(keys[repeat], {})
                data = processAllLevel(
                    keys, value, data[keys[repeat]], repeat + 1, isLastArr)

        def powerVersion(data):
            result = {}
            for key, value in data.items():
                if isValid(key) == True:
                    if len(key.split('.')) >= 3:
                        processAllLevel(key.split('.'), value, result)
            return result

        self.newData = powerVersion(data)

        return self.newData


    def filterTagsParameter(self, data):

        for key, value in data.items():
            newDict = {}
            if 'tags' in key and '%' not in key and '.' in key:
                newDict[key.split('tags.')[1]] = value
                self.newData.setdefault(key.split('.')[0], {}).update(newDict)

        return self.newData