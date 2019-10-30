#!/usr/bin/env python3
import os
import sys
import json
import yaml
import subprocess
import argparse
import copy
import shutil
from jinja2 import Environment, FileSystemLoader

# filter.py
from filter_parameter import filterParameter
import valid

# log.py
import log
import logging
logger = logging.getLogger('Terrain')


def createProvider(**kwargs):

    outputDir = kwargs.get('output_dir', './test/')
    region = kwargs.get('region', 'ap-northeast-1')
    profileFile = kwargs.get('profile_file', '')
    profileName = kwargs.get('profile_name', '')
    parseVar = {'region': region, 'profile_file': profileFile,
                'profile_name': profileName}

    templateLoader = FileSystemLoader(searchpath='templates')
    templateEnv = Environment(loader=templateLoader)
    template = templateEnv.get_template('aws_provider.j2')
    output = template.render(parseVar=parseVar)

    file = open(outputDir + '/aws_provider.tf', 'w')
    file.write(output)
    file.close()


def createEnv(**kwargs):

    region = kwargs.get('region', 'ap-northeast-1')
    accessKeyId = kwargs.get('access_key_id', '')
    secretAccessKey = kwargs.get('secret_access_key', '')
    env = {'AWS_ACCESS_KEY_ID': accessKeyId,
           'AWS_SECRET_ACCESS_KEY': secretAccessKey, 'AWS_DEFAULT_REGION': region}

    return env


def parseJinja(data, **config):

    logger.debug('Input for Jinja parse:')
    logger.debug(json.dumps(data, indent=4, sort_keys=True))
    logger.debug('Configuration for Jinja parse:')
    logger.debug(json.dumps(config, indent=4, sort_keys=True))

    resourceConfig = config.get('config')
    resouceTemplate = resourceConfig.get(
        'resouce_template', 'resouce_template.j2')
    outputFile = resourceConfig.get('output_file', 'resource_template.tf')
    outputDir = resourceConfig.get('output_dir', './')
    outputPath = outputDir + outputFile
    modeCreation = resourceConfig.get('mode_creation', 'a')

    env = Environment(
        loader=FileSystemLoader('templates'),
    )
    template = env.get_template(resouceTemplate)
    output = template.render(terrainData=data)

    # Workaround remove
    output = output.replace(']"', ']')
    output = output.replace('"[', '[')
    output = output.replace("'", '"')
    outputFile = open(outputPath, modeCreation)
    outputFile.write(output)
    outputFile.close()


def cretateAwsResourceTemplate(**config):

    newConfig = copy.deepcopy(config)
    resourceConfig = newConfig.get('config')
    resourceConfig.update({'resouce_template': 'aws_resource.j2'})
    resourceConfig.update({'mode_creation': 'w'})

    resource_type = resourceConfig.get('resource_type', 'aws_instance')
    resource_name = resourceConfig.get('resource_name', 'main')
    args = [{'resource_type': resource_type, 'resource_name': resource_name}]

    parseJinja(args, config=resourceConfig)


def transformAwsResourceParameter(data, **config):

    resourceConfig = config.get('config')
    resourceType = resourceConfig.get('resource_type', '')
    resourceName = resourceConfig.get('resource_name', '')
    resource = resourceType + '.' + resourceName

    # Validate
    validKey = valid.getValidParameter(resourceType)
    restrictionParameter = valid.getRestrictionParameter()
    validParameter = valid.validateParameter(
        data.get(resource).get("primary").get("attributes"), validKey, restrictionParameter)

    terrainSpecialData = {'resource_type': resourceType,
                          'resource_name': resourceName}

    terrainMappingParameter = filterParameter().filterMappingParameter(validParameter)
    terrainArrayParameter = filterParameter().filterArrayParameter(validParameter)
    terrainKeyValueParameter = filterParameter().filterKeyValueParameter(validParameter)
    terrainTagsParameter = filterParameter().filterTagsParameter(validParameter)

    logger.debug('Mapping type:')
    logger.debug(json.dumps(terrainMappingParameter, indent=4, sort_keys=True))
    logger.debug('Array type:')
    logger.debug(json.dumps(terrainArrayParameter, indent=4, sort_keys=True))
    logger.debug('KeyValue type:')
    logger.debug(json.dumps(terrainKeyValueParameter,
                            indent=4, sort_keys=True))
    logger.debug('For tags:')
    logger.debug(json.dumps(terrainTagsParameter, indent=4, sort_keys=True))

    args = (terrainSpecialData, terrainKeyValueParameter,
            terrainArrayParameter, terrainMappingParameter, terrainTagsParameter)

    return args


def readConfiguration(confPath):

    try:
        stream = open(confPath, 'r')
        configurationData = yaml.safe_load(stream)
        logger.debug('Configuration Data:')
        logger.debug(json.dumps(configurationData, indent=4, sort_keys=True))
    except:
        logger.error('Could not read configuration file: %s!', confPath)
        sys.exit()

    return configurationData


def importAwsResource(**config):

    resourceConfig = config.get('config')
    env = config.get('env')

    authMethod = env.get('auth_method', 'env')
    region = env.get('region', 'ap-northeast-1')
    accessKeyId = env.get('access_key_id', '')
    secretAccessKey = env.get('secret_access_key', '')
    profileFile = env.get('profile_file', '')
    profileName = env.get('profile_name', '')
    terraform = env.get(
        'terraform_path', '/usr/local/opt/terraform@0.11/bin/terraform')

    awsResourceType = resourceConfig.get('resource_type', '')
    awsResourceName = resourceConfig.get('resource_name', '')
    awsResourceId = resourceConfig.get('resource_id', '')
    outputDir = resourceConfig.get('output_dir', './test/')
    outputFile = resourceConfig.get('output_file', '/resource_template.tf')

    if authMethod == 'env':
        env = createEnv(region=region, access_key_id=accessKeyId,
                        secret_access_key=secretAccessKey)
    elif authMethod == 'profile':
        env = createProvider(output_dir=outputDir, region=region,
                             profile_file=profileFile, profile_name=profileName)

    if not os.path.exists(outputDir + '/.terraform'):
        shutil.copytree('.terraform', outputDir + '/.terraform')

    subprocessInit = subprocess.Popen(
        [terraform, 'init'], cwd=outputDir, stdout=subprocess.PIPE)
    subprocessInit.communicate()

    awsResourceInput = awsResourceType + '.' + awsResourceName
    subprocessImport = subprocess.Popen(
        [terraform, 'import', awsResourceInput, awsResourceId], cwd=outputDir, stdout=subprocess.PIPE, env=env)
    subprocessImport.communicate()

    # Workaround for removing security group rule
    subprocessStateList = subprocess.Popen(
        [terraform, 'state', 'list'], cwd=outputDir, stdout=subprocess.PIPE, env=env)
    stdout, stderror = subprocessStateList.communicate()
    listStateResult = stdout.decode('ascii').splitlines()
    securityGroupRuleList = [terraform, 'state', 'rm']
    for value in listStateResult:
        if 'aws_security_group_rule' in value:
            securityGroupRuleList.append(value)

    if len(securityGroupRuleList) > 3:
        subprocessStateRemove = subprocess.Popen(
            securityGroupRuleList, cwd=outputDir, stdout=subprocess.PIPE, env=env)
        subprocessStateRemove.communicate()

    os.remove(outputDir + outputFile)


def getTerraformConfigFromFile(**config):

    resourceConfig = config.get('config')
    outputDir = resourceConfig.get('output_dir', './test/')
    terraformStateDir = outputDir + '/terraform.tfstate'
    terraformState = open(terraformStateDir, 'r')
    terraformStateJson = json.load(terraformState)

    resources = terraformStateJson.get("modules")[0].get("resources")

    return resources


def checkOutputDir(value):

    try:
        if value.endswith('.tf'):
            outputDir = os.path.split(value)[0]
            outputFile = '/' + os.path.split(value)[1]
            if not os.path.isdir(outputDir):
                os.makedirs(outputDir)
        else:
            outputFile = '/resource_template.tf'
            outputDir = value
            if not os.path.isdir(value):
                os.makedirs(value)
    except:
        logger.error('Cannot create output directory !!!')
        sys.exit()

    return {'output_dir': outputDir, 'output_file': outputFile}

def createRemoteStateConfig(outputDir, remoteStatePath, data):

    data.update({'key':remoteStatePath})
    templateLoader = FileSystemLoader(searchpath='templates')
    templateEnv = Environment(loader=templateLoader)
    template = templateEnv.get_template('remote_state_config.j2')
    output = template.render(parseVar=data)

    file = open(outputDir + '/remote_state_config.tf', 'w')
    file.write(output)
    file.close()

def pushToRemote(**config):
    resourceConfig = config.get('config')
    env = config.get('env')

    authMethod = env.get('auth_method', 'env')
    region = env.get('region', 'ap-northeast-1')
    accessKeyId = env.get('access_key_id', '')
    secretAccessKey = env.get('secret_access_key', '')
    profileFile = env.get('profile_file', '')
    profileName = env.get('profile_name', '')
    terraform = env.get(
        'terraform_path', '/usr/local/opt/terraform@0.11/bin/terraform')

    outputDir = resourceConfig.get('output_dir', './test/')

    if authMethod == 'env':
        env = createEnv(region=region, access_key_id=accessKeyId,
                        secret_access_key=secretAccessKey)
    elif authMethod == 'profile':
        env = createProvider(output_dir=outputDir, region=region,
                             profile_file=profileFile, profile_name=profileName)

    subprocessInit = subprocess.Popen(
        [terraform, 'init', '-force-copy'], cwd=outputDir, stdout=subprocess.PIPE)
    subprocessInit.communicate()

def init():

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--conf-path',
                        default="terrain.yaml", help="configuration path")
    log.__add_options(parser)
    args = parser.parse_args()
    log.__process_options(parser, args)

    confPath = args.conf_path
    confData = readConfiguration(confPath)

    for value in confData.get('resource'):
        outputPath = checkOutputDir(value.get('output_path'))
        value.update(outputPath)
        cretateAwsResourceTemplate(config=value)
        importAwsResource(config=value, env=confData.get('env'))

    for value in confData.get('resource'):

        resourceData = getTerraformConfigFromFile(config=value)
        resourceParameter = transformAwsResourceParameter(
            resourceData, config=value)
        parseJinja(resourceParameter, config=value)

    if 'remote_state' in confData:
        for value in confData.get('resource'):
            remoteStateConfig = confData.get('remote_state')
            outputDir = value.get('output_dir')
            remoteStatePath = value.get('remote_state_path', '')
            createRemoteStateConfig(outputDir, remoteStatePath, remoteStateConfig)
            pushToRemote(config=value, env=confData.get('env'))

    logger.info('Done !!!')


if __name__ == "__main__":
    init()
