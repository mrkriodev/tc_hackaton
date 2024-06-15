import re
import subprocess
import asyncio
import os
import yaml

import browniecheck

def run_brownie_transfer_check(version) -> bool:
    try:
        # Set the solc version
        subprocess.run(['solc-select', 'use', version], check=True)
        print(f"Successfully set solc version to {version}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to set solc version {version}: {e}")
        return False

def chroot_to_brownie_subfolder(subsubfolder = ""):
    # Get the current folder
    current_folder = os.getcwd()
    subfolder = "browniecheck"
    if len(subsubfolder) > 0:
        os.chdir(os.path.join(os.path.join(current_folder, "src"), subfolder, subsubfolder))
    else:
        os.chdir(os.path.join(os.path.join(current_folder, "src"), subfolder))
    # print(f"chdir to {os.getcwd()}")

def chroot_to_src_folder(up_str="../../"):
    os.chdir(up_str)

async def get_brownie_ouput(file_path):
    chroot_to_brownie_subfolder()
    # Prepare the command
    command = f"brownie run {file_path.replace('.py', '')}.py"
    print(f"Running command: {command}")

    # Run the command and capture the output
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for the command to complete
    stdout, stderr = await process.communicate()

    # Create a dictionary to store the results
    results = {
        'output': '',
        'errors': '',
        'has_error': False
    }

    # Decode and store the output
    if stdout:
        results['output'] = stdout.decode()
    if stderr:
        results['errors'] = stderr.decode()
        results['has_error'] = True
    
    chroot_to_src_folder()
    return results


def generate_brownie_config(net_params_config):
    chroot_to_brownie_subfolder()
    with open('brownie-config.yaml', 'w') as f:
        yaml.dump(net_params_config, f, sort_keys=False)
    chroot_to_src_folder()

    
def append_main_function(contract_adr: str, holder_adr: str, provider: str):
    chroot_to_brownie_subfolder("scripts")
    # with open("check_tranfer.py", "a") as f:
    #     f.write(f"\n\ndef main():\n\ttest_transfer_for_scam({contract_adr}, {holder_adr}, {provider}\n")
    print(os.getcwd())
    with open("check_transfer.py", "r") as f:
        code = f.read()
    # Regex to find and replace the parameters in the test_transfer_for_scam call within main function
    new_code = re.sub(
        r'(test_transfer_for_scam\(")([^"]*)(", ")([^"]*)(", ")([^"]*)("\))',
        fr'\g<1>{contract_adr}\g<3>{holder_adr}\g<5>{provider}\g<7>',
        code
    )
    
    with open("check_transfer.py", "w") as f:
        f.write(new_code)
    chroot_to_src_folder("../../../")