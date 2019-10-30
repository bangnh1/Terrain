#!/usr/bin/env python3

import json
import copy

def getValidParameter(resource):

    validParameterTemplate = open('valid_parameter.json', 'r')
    validParameterJson = json.load(validParameterTemplate)

    validParameter = validParameterJson.get(resource, '')

    return validParameter

def getRestrictionParameter():

    restrictionParameterTemplate = open('restriction_parameter.json', 'r')
    restrictionParameterJson = json.load(restrictionParameterTemplate)
    restrictionParameter = restrictionParameterJson.get('restrictionParameter', '')

    return restrictionParameter


def validateParameter(data, validParamter, restrictionParameter):

    newData = {}
    newDict = {}
    for key, value in data.items():
        for parameter in validParamter:
            if parameter in key:
                newDict[key] = value

    newData = copy.deepcopy(newDict)
    for key, value in newDict.items():
        for parameter in restrictionParameter:
            if parameter in key:
                del newData[key]

    return newData