# Terrain

A tool convert AWS infrastructure to Terraform code

## How tools work

```
Terraform import => terraform.tfstate => filter/transform => terraform code
```

## Requirement

```
- Terraform 0.11
- python3
```

## How to use

```
git clone https://github.com/bangnh1/Terrain.git
cd ~/Terrain
pip install -r requirements.txt

## Download terraform provider aws:
MacOSX:
curl https://releases.hashicorp.com/terraform-provider-aws/2.33.0/terraform-provider-aws_2.33.0_darwin_amd64.zip -o terraform-provider-aws_2.33.0_darwin_amd64.zip
unzip terraform-provider-aws_2.33.0_darwin_amd64.zip
mkdir -p .terraform/plugins/darwin_amd64
cp terraform-provider-aws_v2.33.0_x4 .terraform/plugins/darwin_amd64/

Linux:
curl https://releases.hashicorp.com/terraform-provider-aws/2.33.0/terraform-provider-aws_2.33.0_linux_amd64.zip -o terraform-provider-aws_2.33.0_darwin_amd64.zip
unzip terraform-provider-aws_2.33.0_linux_amd64.zip
mkdir -p .terraform/plugins/linux_amd64
cp terraform-provider-aws_v2.33.0_x4 .terraform/plugins/linux_amd64/

## Modify terrain.example.env.yaml of terrain.example.auth.yaml
mv terrain.example.env.yaml terrain.yaml

python3 main.py --help                                                                                                             
usage: terrain [-h] [-c CONF_PATH] [-v LEVEL]

optional arguments:
  -h, --help            show this help message and exit
  -c CONF_PATH, --conf-path CONF_PATH
                        configuration path
  -v LEVEL, --log-level LEVEL
                        Amount of detail in build-time console messages. LEVEL
                        may be one of TRACE, DEBUG, INFO, WARN, ERROR,
                        CRITICAL (default: INFO).
```

```
Example:

python3 main.py -c terrain.yaml
```

## Supported resources

```
aws_instance
aws_launch_template
aws_launch_configuration
aws_autoscaling_group
aws_security_group
aws_security_rule
aws_route_table
aws_route_table_association
aws_network_acl
aws_internet_gateway
aws_nat_gateway
aws_subnet
aws_vpc
aws_s3_bucket
aws_eip
aws_elb
aws_lb
aws_ecs_cluster
aws_ecs_task_definition
aws_db_instance
aws_db_parameter_group
aws_db_option_group
aws_db_subnet_group
aws_rds_cluster
aws_rds_cluster_instance
aws_rds_cluster_parameter_group
```

## How to add more resources:

```
- Add valid parameter in valid_parameter.json
- Add parameters you want to restrict in restriction_parameter.json
```

### Limitations

```
- aws_ecs_cluster: Have to add "" to volume's value parameter
```
