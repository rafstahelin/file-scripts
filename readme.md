Config Manager v1.0-release
A command-line tool for managing configuration folders and datasets efficiently. The Config Manager simplifies the process of creating new configurations based on existing ones or templates, ensuring consistency and reducing manual effort.

Table of Contents
Features
Requirements
Installation
Usage
Examples
License
Features
Interactive CLI: User-friendly command-line interface for easy navigation.
Folder Management: Create new configuration folders based on existing ones or predefined templates.
Dataset Selection: Choose datasets from available options, grouped and displayed neatly.
Automated Updates: Automatically update configuration files with new token names and versions.
Cross-Platform Support: Works on Unix-like systems and Windows.
Requirements
Python 3.6 or higher
Rich library for enhanced console output
Installation
Clone the repository (if applicable) or download the config_manager.py script.

Install the required Python package:

bash
Copy code
pip install rich
Usage
Run the script from the command line:

bash
Copy code
python config_manager.py
Follow the on-screen prompts to create or manage configuration folders.

Steps:
Select Source Folder Type:

Use an existing folder.
Use the 'lora' template.
Use the 'lokr' template.
Select Source Folder or Enter Token Name:

If using an existing folder, select from the displayed list.
If using a template, enter the new token name.
Enter Version Number:

Specify the new version number for the configuration.
Select Dataset:

Choose whether to use the same dataset or select a new one from the displayed list.
Confirm and Proceed:

Review the parameters and confirm to proceed.
The script will copy files and update configuration files automatically.
Examples
Creating a New Configuration from an Existing Folder
plaintext
Copy code
=== Configuration Folder Management Tool ===

Select source folder type:
1. Use existing folder
2. Use 'lora' template
3. Use 'lokr' template
Enter choice: 1

Existing folders:
[Displays folders in organized panels]

Enter number to select source folder: 3
Enter new version number: 04
Use same dataset? [y/n]: n

Available datasets:
[Displays datasets in organized panels]

Enter dataset number: 6

Processing with following parameters:
Source Directory: lora-03
Token Name: lora
New Version: 04
New Folder Name: lora-04
Dataset: lulu-15

Proceed? [y/n]: y

Copying files...
Updating configuration files...

Operation completed successfully!

Created new configuration in: lora-04
License
This project is licensed under the MIT License. See the LICENSE file for details.
