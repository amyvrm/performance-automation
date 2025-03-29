import boto3
import argparse

def delete_ec2_instances(instance_ids, region_name='us-east-1'):
    # Create an EC2 client
    ec2_client = boto3.client('ec2', region_name=region_name)

    try:
        # Terminate the instances
        response = ec2_client.terminate_instances(InstanceIds=instance_ids)
        print("Termination initiated for instances:", instance_ids)
        print("Response:", response)
    except Exception as e:
        print("Error terminating instances:", e)

# Example usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Please give argument to perform operations')
    parser.add_argument('--ids', type=str, help="Html file name")
    args = parser.parse_args()

    instance_ids_to_delete = args.ids.split(',')
    instance_ids_to_delete = [instance_id.strip() for instance_id in instance_ids_to_delete]  # Remove any extra spaces

    print(f"Instance IDs to delete: {instance_ids_to_delete}")
    
    # Call the function to delete the instances
    delete_ec2_instances(instance_ids_to_delete)