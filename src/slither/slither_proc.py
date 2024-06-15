import asyncio
from calendar import c
import subprocess
import os
from typing import Optional, Tuple
import re
import requests
import json
import aiofiles
from packaging import version

ETHERSCAN_API_KEY="DUQ3IPIYBDIDQCW6XTIF5HZ6HGF4III6CV"
BSCSCAN_API_KEY="CH6W15GK3EDH3W13IJFAHNZY37GMYZ8NM7"
pragma_pattern_simple_version = r'pragma solidity (?:\^|>=|=?)?(\d+\.\d+\.\d+);'
# pragma_pattern_simple_version = r'pragma solidity (?:\^|>=|=?)?(\d+\.\d+\.\d+)\s*;'
pragma_pattern_complex_version = r'pragma solidity\s*(?:\^|>=?)?(\d+\.\d+\.\d+)\s*<\s*(\d+\.\d+\.\d+);'
# pragma_pattern_complex_version = r'pragma solidity\s*(?:\^|>=?)?(\d+\.\d+\.\d+)\s*<\s*(\d+\.\d+\.\d+);'
pragma_pattern_highest_version = r'(?:pragma solidity\s*(?:.*<|=|>=?|\^)?)?(\d+\.\d+\.\d+);'
pragma_pattern = r'pragma solidity (?:\^|>=|=?)?(.*?);'
import_pattern = r'import [^;]+;'


def parse_slither_documentation():
    current_file_path = os.path.abspath(__file__)
    folder_path = os.path.dirname(current_file_path)
    detectors_file = os.path.join(folder_path, "Detector-Documentation.md")
    
    # Reading the contents of the uploaded file
    with open(detectors_file, 'r') as file:
        uploaded_file_content = file.read()

    # Regex pattern to extract the desired information for each section
    pattern = r"## (.*?)\n### Configuration\n\* Check: .+?\n\* Severity: `(.*?)`\n\* Confidence: `(.*?)`"

    # Applying the regex pattern to the file content
    matches_uploaded_file = re.findall(pattern, uploaded_file_content)

    # Creating a list of dictionaries for each section in the uploaded file
    extracted_info_from_uploaded_file = [{'name': str(match[0]).replace("`", "").replace(" ", "-").lower(), 
                                          'severity': match[1], 
                                          'confidence': match[2]} 
                                         for match in matches_uploaded_file]

    return extracted_info_from_uploaded_file

slither_detectors = parse_slither_documentation()

def get_contract_source_code(address, provider)->dict:
    base_url = "https://api.etherscan.io/api?module=contract&action=getsourcecode"
    api_key = ETHERSCAN_API_KEY
    
    if provider == "bsc":
        api_key = BSCSCAN_API_KEY
        base_url = "https://api.bscscan.com/api?module=contract&action=getsourcecode"
        
    full_url = f"{base_url}&address={address}&apikey={api_key}"
    response = requests.get(full_url)
    
    data = response.json()
    source_code = data["result"][0]    
    return source_code


async def analyze_solidity(file_path):
    # Prepare the command
    command = f"slither {file_path}"

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

    return results


async def compile_to_opcode(file_path) -> dict:
    # Prepare the command
    command = f"solc --opcodes {file_path}"

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
    }

    # Decode and store the output
    if stdout:
        results['output'] = stdout.decode()
    if stderr:
        results['errors'] = stderr.decode()

    return results


class MSolcError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class MSolcContentError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
        
class MSolcCompilationError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
        
class MSolcDefinitionError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


def detect_necessary_solc(sol_file_path) -> Tuple[bool, str]:
    command = f"solc --bin {sol_file_path}"
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return (True, str(result.stdout))
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode()
        if 'different compiler version' in error_message:
            print("Error: The Solidity source file requires a different compiler version.")
            # Here, you can add logic to switch the compiler version or give a detailed error message.
        else:
            print("Compilation error:", error_message)
            if str(error_message).find("{\"cont") > -1:
                print("Error: The Solidity source file contains invalid syntax.")
                raise MSolcContentError(error_message) 
            elif str(error_message).find("Expected pragma") > -1:
                raise MSolcError(error_message)
            elif str(error_message).find("Definition of base has to precede") > -1:
                raise MSolcDefinitionError(error_message)
            # elif str(error_message).find("but got") > -1 :
            #     raise MSolcCompilationError(error_message)
            else:
                raise Exception(error_message)
        return (False, error_message)


def get_solidity_version_from_error_msg(error_str):
    match = re.search(pragma_pattern_simple_version, error_str)
    if match:
        return str(match.group(1))
    else:
        match = re.search(pragma_pattern_highest_version, error_str)
        if match:
            return str(match.group(1))
    return None

def get_supported_solc_versions():
    # Run the solc-select versions command and capture its output
    result = subprocess.run(['solc-select', 'versions'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Decode the output from bytes to a string
    output = result.stdout.decode()
    # Regular expression to match version numbers
    pattern = r'(\d+\.\d+\.\d+)'
    # Find all matches in the output
    versions = re.findall(pattern, output)
    return versions

def install_solc_version(version) -> bool:
    try:
        # Execute the solc-select install command for the specified version
        subprocess.run(['solc-select', 'install', version], check=True)
        print(f"Successfully installed solc version to {version}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install solc version {version}: {e}")
        return False


def acivate_solc_version(version) -> bool:
    try:
        # Set the solc version
        subprocess.run(['solc-select', 'use', version], check=True)
        print(f"Successfully set solc version to {version}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to set solc version {version}: {e}")
        return False

def parse_slither_output(data):
    # Extracting the total number of results
    results_match = re.search(r'(\d+) result\(s\) found', data['errors'])
    total_results = results_match.group(1) if results_match else 'No results count found'
    
    info_reference_pairs = re.findall(r'INFO:Detectors:(.+?)Reference: (.+?)(?=\r\nINFO:|\r\nINFO:Slither|$)', data['errors'], re.DOTALL)
    # Structuring the extracted information
    ref_info = []
    for info, url in info_reference_pairs:
        issue_info = info.strip()
        url = url.strip()
        ref_info.append({'url': url, 'issue': issue_info})
    
    return {'total_results': total_results, 'references': ref_info}


def concatanate_contract_content(sol_content_data)->str:    
    # Initialize an empty string to hold the concatenated content
    concatenated_content = ""
    pragma_added = False
    highest_pragma_version = ""
    # Iterate over each contract in the 'sources' and concatenate their content
    for contract_path, contract_data in sol_content_data.items():
        content_lines = contract_data['content'].split('\\n')
        for line in content_lines:
            #if line.startswith('pragma solidity') and not pragma_added:
            pragma_pattern_complex_version_match = re.search(pragma_pattern_complex_version, line)
            if pragma_pattern_complex_version_match:
                content = re.sub(pragma_pattern_complex_version, '', line, count=1)
                # Not remove comments
                comments_at_begin_pattern = r'^(///|//|/\*\*?).*'
                if not re.match(comments_at_begin_pattern, content):
                    content = content[2:]
                # Remove the import statements
                modified_content = re.sub(import_pattern, '', content)
                concatenated_content += modified_content + '\n'
            # if (pragma_index := line.find("pragma solidity")) != -1 and not pragma_added:
            #     modified_content = re.sub(import_pattern, '', line)
            #     concatenated_content += modified_content + '\n'
            #     pragma_added = True
            elif (pragma_pattern_simple_version_match := re.search(pragma_pattern_simple_version, line)) and not pragma_added:
                highest_pragma_version = pragma_pattern_simple_version_match.group(1)
                pragma_string = f"pragma solidity {pragma_pattern_simple_version_match.group(1)};"
                concatenated_content = (pragma_string + '\n' + concatenated_content)
                content = re.sub(pragma_pattern_simple_version, '', line, count=1)
                # Not remove comments
                comments_at_begin_pattern = r'^(///|//|/\*\*?).*'
                if not re.match(comments_at_begin_pattern, content):
                    content = content[2:]
                modified_content = re.sub(import_pattern, '', content)
                concatenated_content += modified_content + '\n'
                pragma_added = True
            elif (pragma_pattern_simple_version_match := re.search(pragma_pattern_simple_version, line)) and pragma_added:
                cur_veriosn = pragma_pattern_simple_version_match.group(1)
                if version.parse(cur_veriosn) > version.parse(highest_pragma_version):
                    highest_pragma_version = cur_veriosn
                    concatenated_content = re.sub(pragma_pattern, f"pragma solidity {cur_veriosn};", concatenated_content)
                modified_content = re.sub(pragma_pattern, '', line, count=1)
                modified_content2 = modified_content
                # Not remove comments
                comments_at_begin_pattern = r'^(///|//|/\*\*?).*'
                if not re.match(comments_at_begin_pattern, modified_content):
                    modified_content2 = modified_content[2:]
                # Remove the import statements
                modified_content3 = re.sub(import_pattern, '', modified_content2)
                # Add other lines normally
                concatenated_content += modified_content3 + '\n'
            elif line.startswith('pragma solidity') and pragma_added:
                content = re.sub(pragma_pattern, '', line, count=1)
                content = content[2:]
                # Remove the import statements
                modified_content = re.sub(import_pattern, '', content)
                concatenated_content += modified_content + '\n'
            elif (pragma_index := line.find("pragma solidity")) != -1:
                #modified_content = line[pragma_index:]
                modified_content = re.sub(pragma_pattern, '', line, count=1)
                # modified_content2 = re.sub(pragma_pattern, '', modified_content, count=1)
                modified_content2 = modified_content
                # Not remove comments
                comments_at_begin_pattern = r'^(///|//|/\*\*?).*'
                if not re.match(comments_at_begin_pattern, modified_content):
                    modified_content2 = modified_content[2:]
                # Remove the import statements
                modified_content3 = re.sub(import_pattern, '', modified_content2)
                # Add other lines normally
                concatenated_content += modified_content3 + '\n'
            else:
                # Add other lines normally
                concatenated_content += line + '\n'

        concatenated_content += '\n// End of ' + contract_path + '\n\n'
    
    return concatenated_content


def reorder_solidity_definitions_v4(solidity_code):
    # Correcting the issue with the f-string in the lambda function
    transformed_solidity_code = re.sub(
        r'\ninterface\s+(\w+)\s+is\s*(.*?){',
        lambda m: '\ninterface ' + m.group(1) + ' is ' + ' '.join(m.group(2).split()) + ' {',
        solidity_code,
        flags=re.DOTALL
    )
    solidity_code = transformed_solidity_code
    # Regular expression pattern to identify contract, interface, library, and abstract contract definitions
    definition_pattern = r'(contract|interface|abstract contract|library)\s+(\w+)(\s+is\s+[\w\s,]+)?\s*{'
    # Extracting all definitions
    definitions = re.findall(definition_pattern, solidity_code)

    # Creating maps for each definition with its code and dependencies
    library_map = {}
    other_definition_map = {}
    for def_type, name, inheritance in definitions:
        # Extracting the full definition
        full_definition_pattern = rf'{def_type}\s+{name}\b.*?{{[\s\S]*?\n}}'
        full_definition_match = re.search(full_definition_pattern, solidity_code)
        
        if full_definition_match:
            full_definition = full_definition_match.group(0)
            # Extracting dependencies
            dependencies = re.findall(r'\b(\w+)\b', inheritance)
            if def_type == 'library':
                library_map[name] = full_definition
            else:
                other_definition_map[name] = {
                    'code': full_definition,
                    'dependencies': dependencies
                }

    # Function to add definitions in sorted order, excluding libraries
    sorted_definitions = []

    def add_definition(name):
        if name in sorted_definitions or name not in other_definition_map:
            return
        for dep in other_definition_map[name]['dependencies']:
            add_definition(dep)
        sorted_definitions.append(name)

    # Sorting the definitions, excluding libraries
    for name in other_definition_map:
        add_definition(name)

    # Libraries will be always on top, followed by other definitions
    sorted_code = '\n\n'.join(library_map.values()) + '\n\n' + '\n\n'.join(other_definition_map[name]['code'] for name in sorted_definitions)
    return sorted_code

def move_open_braces_to_previous_line(s):
    lines = s.splitlines()
    modified_lines = []

    for i in range(len(lines)):
        if lines[i].strip() == '{' and modified_lines:
            modified_lines[-1] = modified_lines[-1] + ' {'
        else:
            modified_lines.append(lines[i])

    return '\n'.join(modified_lines)


async def prepare_sol_file_and_solc_compiler(sol_file_path):
    # current_file_path = os.path.abspath(__file__)
    # folder_path = os.path.dirname(current_file_path)
    # sol_file = os.path.join(folder_path, f"{contract_address}.sol")
    
    all_tries_done = False
    result = False
    str = ""
    while(not all_tries_done):
        try:
            result, str = detect_necessary_solc(sol_file_path)
            all_tries_done = True
        except MSolcError as mse:
            # try to get internal sources:
            #data_string  = source_code['SourceCode']
            with open(sol_file_path, "r", encoding="utf-8") as f:
                data_string = f.read()
            # Parse the string into a dictionary
            all_tries_done_two = False
            while(not all_tries_done_two):
                try:
                    data_dict :dict = json.loads(data_string)
                    # Access the 'sources' item
                    if 'sources' in data_dict:
                        sources = data_dict['sources']
                        all_tries_done_two = True
                        with open(sol_file_path, "w", encoding="utf-8") as f:
                            f.write(json.dumps(sources))
                    else:
                        contracts_concatenated_string = concatanate_contract_content(data_dict)
                        
                        # Removing single-line comments
                        solidity_code_no_single_line_comments = re.sub(r'//.*', '', contracts_concatenated_string)
                        # Removing multi-line comments
                        solidity_code_no_comments = re.sub(r'/\*[\s\S]*?\*/', '', solidity_code_no_single_line_comments)
                        solidity_code_no_comments_with_moved_braces = move_open_braces_to_previous_line(solidity_code_no_comments)
                        
                        contracts_concatenated_string = solidity_code_no_comments_with_moved_braces
                        #contracts_concatenated_string = ''.join([value['content'] for value in data_dict.values()])
                        with open(sol_file_path, "w", encoding="utf-8") as f:
                            for line in contracts_concatenated_string.splitlines():
                                if line.strip():
                                    f.write(line + '\n')
                            #f.write(contracts_concatenated_string)
                        all_tries_done_two = True
                except json.JSONDecodeError as je:
                    data_string = data_string[1:-1]
                    continue
                except Exception as e:
                    print(f"Error: {e}")
                    all_tries_done_two = True
                    continue
        except MSolcContentError as msce:
            with open(sol_file_path, "r", encoding="utf-8") as f:
                data_content = json.load(f)
            sol_content = concatanate_contract_content(data_content)
            # Removing single-line comments
            solidity_code_no_single_line_comments = re.sub(r'//.*', '', sol_content)
            # Removing multi-line comments
            solidity_code_no_comments = re.sub(r'/\*[\s\S]*?\*/', '', solidity_code_no_single_line_comments)
            solidity_code_no_comments_with_moved_braces = move_open_braces_to_previous_line(solidity_code_no_comments)
            with open(sol_file_path, "w", encoding="utf-8") as fout:
                for line in solidity_code_no_comments.splitlines():
                    if line.strip():
                        fout.write(line + '\n')
                    # f.write(sol_content)
        except MSolcDefinitionError as msde:
            with open(sol_file_path, "r", encoding="utf-8") as f:
                solidity_code = f.read()
            solidity_code_no_comments = re.sub(r'/\*[\s\S]*?\*/', '', solidity_code)
            solidity_code_no_comments_with_moved_braces = move_open_braces_to_previous_line(solidity_code_no_comments)
            
            solidity_code = solidity_code_no_comments_with_moved_braces
            # Reordering the Solidity definitions
            pragma_verion_string_match = re.search(pragma_pattern_simple_version, solidity_code)
            pragma_string = "pragma solidity ^0.8.0;"
            if pragma_verion_string_match:
                pragma_string = f"pragma solidity {pragma_verion_string_match.group(1)};"
            reordered_solidity_code = pragma_string + "\n" + reorder_solidity_definitions_v4(solidity_code)
            with open(sol_file_path, "w", encoding="utf-8") as f:
                f.write(reordered_solidity_code)
            # all_tries_done = True
        except Exception as e:
            print(f"Error: {e}")
            all_tries_done = True
        
    if(result == False):
        # print(f"error_message = {str}")
        version = get_solidity_version_from_error_msg(str)
        if version is None:
            return None
        supported_versions = get_supported_solc_versions()
        if version not in supported_versions:
            print(f"Error: The Solidity source file requires a different compiler version. Supported versions: {supported_versions}")
            # try to install new version of solc
            if not install_solc_version(version):
                return None
        if not acivate_solc_version(version):
            return None
        
    return sol_file_path


async def contract_source_code_analytic(contrac_address, provider, source_code = None) -> dict:
    if source_code is None:
        source_code = get_contract_source_code(contrac_address, provider)
        
    temp_dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
    os.makedirs(temp_dir_path, exist_ok=True)
    base_sol_file_path = os.path.join(temp_dir_path, f"{contrac_address}.sol")
    
    with open(base_sol_file_path, "w", encoding="utf-8") as f:
        f.write(source_code['SourceCode'])
    
    acivate_solc_version("0.8.19")
    
    sol_file_path = await prepare_sol_file_and_solc_compiler(base_sol_file_path)
    if sol_file_path is None:
        return {}
    
    already_msde_raised = False
    
    while(True):
        try:
            analysis_results = await analyze_solidity(sol_file_path)
            
            has_error = analysis_results.get("has_error", False)
            if has_error:
                parsed_errors_data = parse_slither_output(analysis_results)
                
                if parsed_errors_data['total_results'] == "No results count found":
                    if already_msde_raised:
                        analysis_results['not_compiled'] = True
                        break
                    else:
                        already_msde_raised = True
                        raise MSolcDefinitionError("Something wrong. Try to rebase code")
                
                print(f"Total results: {parsed_errors_data['total_results']}")
                for ref in parsed_errors_data['references']:
                    print(f"URL: {ref['url']}")

                # enriched_erros_data_output = enrich_parsed_data(parsed_errors_data)
                # analysis_results['enriched_erros_data_output'] = enriched_erros_data_output
            break
        except MSolcDefinitionError as msde:
            with open(sol_file_path, "r", encoding="utf-8") as f:
                solidity_code = f.read()
            # Reordering the Solidity definitions
            pragma_verion_string_match = re.search(pragma_pattern_simple_version, solidity_code)
            pragma_string = "pragma solidity ^0.8.0;"
            if pragma_verion_string_match:
                pragma_string = f"pragma solidity {pragma_verion_string_match.group(1)};"
            reordered_solidity_code = pragma_string + "\n" + reorder_solidity_definitions_v4(solidity_code)
            with open(sol_file_path, "w", encoding="utf-8") as f:
                f.write(reordered_solidity_code)
            continue
    
    return analysis_results


def extract_opcodes(text):
    sections_to_exclude = ['Context', 'ERC20', 'Ownable', 'IERC20', 'Address']
    pattern = r"======= src/slither/temp/0x[0-9a-fA-F]{40}.sol:(\w+) =======\r?\nOpcodes:\r?\n([\s\S]*?)(?=\r?\n=======|\Z)"
    matches = re.findall(pattern, text.strip())
    
    opcodes = []
    for section, opcode in matches:
        if section not in sections_to_exclude:
            opcodes.append(opcode.strip())
    
    return "\n\n".join(opcodes)


async def source_code_to_opcodes(contrac_address, provider, source_code = None) -> Optional[str]:
    temp_dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
    os.makedirs(temp_dir_path, exist_ok=True)
    base_sol_file_path = os.path.join(temp_dir_path, f"{contrac_address}.sol")
    
    if not os.path.exists(base_sol_file_path):
        if source_code is None:
            source_code = get_contract_source_code(contrac_address, provider)
        with open(base_sol_file_path, "w", encoding="utf-8") as f:
            f.write(source_code['SourceCode'])
    
    acivate_solc_version("0.8.19")
    
    sol_file_path = await prepare_sol_file_and_solc_compiler(base_sol_file_path)
    if sol_file_path is None:
        return None
    
    already_msde_raised = False
    analysis_results = {}
    while(True):
        try:
            analysis_results = await analyze_solidity(sol_file_path)
            
            has_error = analysis_results.get("has_error", False)
            if has_error:
                parsed_errors_data = parse_slither_output(analysis_results)
                
                if parsed_errors_data['total_results'] == "No results count found":
                    if already_msde_raised:
                        analysis_results['not_compiled'] = True
                        break
                    else:
                        already_msde_raised = True
                        raise MSolcDefinitionError("Something wrong. Try to rebase code")
                
                print(f"Total results: {parsed_errors_data['total_results']}")
                for ref in parsed_errors_data['references']:
                    print(f"URL: {ref['url']}")

                # enriched_erros_data_output = enrich_parsed_data(parsed_errors_data)
                # analysis_results['enriched_erros_data_output'] = enriched_erros_data_output
            break
        except MSolcDefinitionError as msde:
            with open(sol_file_path, "r", encoding="utf-8") as f:
                solidity_code = f.read()
            # Reordering the Solidity definitions
            pragma_verion_string_match = re.search(pragma_pattern_simple_version, solidity_code)
            pragma_string = "pragma solidity ^0.8.0;"
            if pragma_verion_string_match:
                pragma_string = f"pragma solidity {pragma_verion_string_match.group(1)};"
            reordered_solidity_code = pragma_string + "\n" + reorder_solidity_definitions_v4(solidity_code)
            with open(sol_file_path, "w", encoding="utf-8") as f:
                f.write(reordered_solidity_code)
            continue
    
    if analysis_results.get('not_compiled', False):
        return None
    
    # компилируем
    solc_result = await compile_to_opcode(sol_file_path)
    # Получение результата
    result = extract_opcodes(solc_result['output'])
    return result.strip()
        

# Example usage
async def main():
    #m_contract_address = "0xc0f1728d9513efc316d0e93a0758c992f88b0809"
    #m_provider = "eth"
    # m_contract_address = "0x9F8a75436e7E808F3Fb348182E0ea42d2dd467Cd"
    # m_provider = "bsc"
    # m_contract_address = "0x3506424f91fd33084466f402d5d97f05f8e3b4af"
    # m_provider = "eth"
    m_contract_address = "0x15b543e986b8c34074dfc9901136d9355a537e7e"
    m_provider = "eth"
    
    temp_dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
    os.makedirs(temp_dir_path, exist_ok=True)
    # base_sol_file_path = os.path.join(temp_dir_path, f"{m_contract_address}.sol")
    
    source_code = get_contract_source_code(m_contract_address, m_provider)
    # with open(base_sol_file_path, "w", encoding="utf-8") as f:
    #     f.write(source_code['SourceCode'])
    
# asyncio.run(main())
