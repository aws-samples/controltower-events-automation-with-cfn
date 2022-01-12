# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

# NOTES
# This function can be adapted to run any code inside a newly created Control Tower 
# Account. In this ****example****,we automatically tag the VPC resources 
# (VPC, Subnets, Route Table, NAT Gateways, Internet Gateways, NACLs, default SG) for 
# any default VPC created by Control Tower so users understand their function. Note 
# that this code leverages the default 'AWSControlTowerExecution' role which is created
# automatically as part of Control Tower account provisioning.

import json
import boto3
import logging
import os
from botocore.exceptions import ClientError
import time

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)
logging.getLogger('boto3').setLevel(logging.CRITICAL)
logging.getLogger('botocore').setLevel(logging.CRITICAL)

session = boto3.Session()

def lambda_handler(event, context):
    LOGGER.info('-----Start Lambda Execution-----')
    LOGGER.info("REQUEST RECEIVED: " + json.dumps(event, default=str))

    # Check Lifecycle Event Pattern for Match - Account Created Successfully
    if 'detail' in event and event['detail']['eventName'] == 'CreateManagedAccount':
        if event['detail']['serviceEventDetails']['createManagedAccountStatus']['state'] == 'SUCCEEDED':
            account_id = event['detail']['recipientAccountId']
            
            
            #Build Role ARN
            execution_role_arn = "arn:aws:iam::" + account_id + ":role/AWSControlTowerExecution"
            
            #Assume Control Tower Execution Role on new account
            sts_client = boto3.client('sts')
            assumed_role_object=sts_client.assume_role(
                RoleArn=execution_role_arn,
                RoleSessionName="AssumeRoleSession"
            )
            LOGGER.info("Control Tower Execution Role ARN: " + execution_role_arn)
            credentials=assumed_role_object['Credentials']
            
            ###########################################
            ###########################################
            ##****CUSTOM CODE START HERE - Example***##
            ###########################################
            ###########################################
            
            ec2_client = boto3.client(
                'ec2',
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken']
            )
            
            # Get list of regions
            regions = [region['RegionName']
                        for region in ec2_client.describe_regions()['Regions']]
            
            # Iterate through each region, setting EC2 client   
            for region in regions:
                LOGGER.info("Currently Selected Region: " + region)
                ec2_client = boto3.client(
                    'ec2',                    
                    region_name=region,
                    aws_access_key_id=credentials['AccessKeyId'],
                    aws_secret_access_key=credentials['SecretAccessKey'],
                    aws_session_token=credentials['SessionToken']
                )

                ##########################
                # Tag VPCs in each region#
                ##########################
                
                # Get VPC Information
                
                # Check if VPC exists
                if ec2_client.describe_vpcs()['Vpcs'] != []:
                    
                    # Get Control Tower VPC Information
                    vpc = ec2_client.describe_vpcs()
                    
                    # Verify subnet is part of Control Tower VPC and then apply name tag
                    vpc_name = "controltower-vpc-" + region
                    vpc_id = vpc['Vpcs'][0]['VpcId']
                    vpc_tag_response = ec2_client.create_tags(Resources=[vpc_id], Tags=[{'Key':'Name', 'Value':vpc_name}])
                    LOGGER.info("Tagging VPC_ID " + vpc_id + " as " + vpc_name)
                    
                else:
                    LOGGER.info("No vpc found in region: " + region)       
                    continue

                #############################
                # Tag Subnets in each region#
                #############################
                
                # Check if subnets exist
                if ec2_client.describe_subnets()['Subnets'] != []:
                    
                    # Zero counter label iterator
                    subnet_counter=0
                    
                    # Loop through each subnet in region and collect information
                    for subnet in ec2_client.describe_subnets()['Subnets']:
                         
                        # Verify subnet is part of Control Tower VPC and then apply name tag
                        if subnet['VpcId'] == vpc_id:
                            az = str(subnet['AvailabilityZone'])
                            subnet_name = vpc_name + "-subnet-az-" + az[-2:]
                            subnet_tag_response = ec2_client.create_tags(Resources=[subnet['SubnetId']], Tags=[{'Key':'Name', 'Value':subnet_name}])
                            LOGGER.info("VPC_ID Match - Labelling Subnet " + subnet['SubnetId'] + " as " + subnet_name)
                        
                        else:
                            LOGGER.error("Subnets not available or does not match Control Tower VPC: " + vpc_id)
                else:
                    LOGGER.info("No subnet(s) found for VPC" + vpc_id + " in " + region)       
                
                ##################################
                # Tag Route Tables in each region#
                ##################################

                # Check if Route Table exists
                if ec2_client.describe_route_tables()['RouteTables'] != []:
                    
                    # Get Control Tower Internet Route Table Information
                    route_table = ec2_client.describe_route_tables()['RouteTables'][0]
                    
                    #Verify route table is part of Control Tower VPC and then apply name tag
                    if route_table['VpcId'] == vpc_id:
                        route_table_name = vpc_name + "-routetable"
                        route_table_tag_response = ec2_client.create_tags(Resources=[route_table['RouteTableId']], Tags=[{'Key':'Name', 'Value':route_table_name}])
                        LOGGER.info("VPC_ID Match - Labelling Route Table " + route_table['RouteTableId'] + " as " + route_table_name)
                        
                    else:
                        LOGGER.error("Route Table VPC not available or does not match Control Tower VPC: " + vpc_id)
                else:
                    LOGGER.info("No route table found for VPC" + vpc_id + " in " + region)             
                    
                #######################################
                # Tag Internet Gateways in each region#
                #######################################

                # Check if Internet Gateway exists
                if ec2_client.describe_internet_gateways()['InternetGateways'] != []:
                    
                    # Get Control Tower Internet Gateway Information
                    internet_gw = ec2_client.describe_internet_gateways()['InternetGateways'][0]
                    
                    #Verify Internet Gateway is part of Control Tower VPC and then apply name tag
                    if internet_gw['Attachments'][0]['VpcId'] == vpc_id:
                        internet_gw_name = vpc_name + "-internetgw"
                        internet_gw_tag_response = ec2_client.create_tags(Resources=[internet_gw['InternetGatewayId']], Tags=[{'Key':'Name', 'Value':internet_gw_name}])
                        LOGGER.info("VPC_ID Match - Labelling Internet Gateway " + internet_gw['InternetGatewayId'] + " as " + internet_gw_name)
                        
                    else:
                        LOGGER.error("Internet Gateway not available or does not match Control Tower VPC: " + vpc_id)
                else:
                    LOGGER.info("No Internet Gateway found for VPC" + vpc_id + " in " + region)               
                    
                    
                ##########################
                # Tag NACL in each region#
                ##########################

                # Check if NACL exists
                if ec2_client.describe_network_acls()['NetworkAcls'] != []:

                    # Get Control Tower NACL Information
                    nacl = ec2_client.describe_network_acls()['NetworkAcls'][0]
                    
                    #Verify NACL is part of Control Tower VPC and then apply name tag
                    if nacl['VpcId'] == vpc_id:
                        nacl_name = vpc_name + "-nacl"
                        nacl_tag_response = ec2_client.create_tags(Resources=[nacl['NetworkAclId']], Tags=[{'Key':'Name', 'Value':nacl_name}])
                        LOGGER.info("VPC_ID Match - Labelling NACL " + nacl['NetworkAclId'] + " as " + nacl_name)
                        
                    else:
                        LOGGER.error("NACL not available or does not match Control Tower VPC: " + vpc_id)
                else:
                    LOGGER.info("No NACLS found for VPC" + vpc_id + " in " + region)                
                    
                ################################
                #Tag NAT Gateway in each region#
                ################################

                
                # Check if NAT gateways exist
                if ec2_client.describe_nat_gateways()['NatGateways'] != []:
                    
                    # Get NAT Gateway ID
                    for nat_gw in ec2_client.describe_nat_gateways()['NatGateways']:
                
                        #Verify NAT Gateway is part of Control Tower VPC 
                        if nat_gw['VpcId'] == vpc_id:
                            
                            #Find subnet az NAT Gateway is in, and use this as part of name tag
                            az = str(ec2_client.describe_subnets(SubnetIds=[nat_gw['SubnetId']])['Subnets'][0]['AvailabilityZone'])[-2:]
                            
                            # Apply name tag
                            nat_gw_name = vpc_name + "-natgw-az-" + az
                            nat_gw_tag_response = ec2_client.create_tags(Resources=[nat_gw['NatGatewayId']], Tags=[{'Key':'Name', 'Value':nat_gw_name}])
                            LOGGER.info("VPC_ID Match - Labelling NAT Gateway " + nat_gw['NatGatewayId'] + " as " + nat_gw_name)
                        else:
                            LOGGER.error("NAT Gateway not available or does not match Control Tower VPC: " + vpc_id)                        
                else:
                    LOGGER.info("No NAT Gateways found for VPC" + vpc_id + " in " + region)
                
                    
            ##########################################
            ##########################################
            ##****CUSTOM CODE END HERE - Example****##
            ##########################################   
            ##########################################
            

        else:
             LOGGER.error("Event not SUCCEEDED, Lambda did not run : " + event)
    else:
        LOGGER.error("Invalid Event - Not Account Creation : " + event)

    LOGGER.info('-----End Lambda Execution-----')

