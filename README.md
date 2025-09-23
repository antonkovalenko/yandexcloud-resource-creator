# Yandex Cloud Resource Creator

A Python CLI for creating and managing Yandex Cloud resources: users, folders/access, VPC networks, YDB databases, password resets, and load script generation.

## Features

- Create users with unique names, validated parameters, and CSV streaming output
- Create personal folders, grant folder Editor and cloud membership access
- Create VPC with 3 subnets (one per zone), or reuse existing VPC
- Create YDB databases (skips if one with storage groups already exists)
- Reset passwords for specified or all users in a userpool (CSV streaming output)
- Generate load scripts for YDB via ydb CLI
- Robust operation polling with retries and timing logs

## Prerequisites

- Python 3.7 or higher
- Yandex Cloud IAM token with appropriate permissions
- Access to Yandex Cloud organization-manager API

## Installation

### 1. Clone or download the project

```bash
# If using git
git clone https://github.com/antonkovalenko/yandexcloud-resource-creator.git
cd yandexcloud-resource-creator

# Or simply navigate to the project directory if you have the files
cd /path/to/yandexcloud-resource-creator
```

### 2. Create and activate a virtual environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate
```

### 3. Install required dependencies

```bash
pip install -r requirements.txt
```

## Configuration

### Set up IAM Token

Set the `IAM_TOKEN` environment variable with your Yandex Cloud IAM token:

```bash
# On macOS/Linux:
export IAM_TOKEN="your_iam_token_here"

# On Windows:
# set IAM_TOKEN=your_iam_token_here
```

**Note:** Replace `your_iam_token_here` with your actual IAM token from Yandex Cloud.

## Usage

All commands require an IAM token in the environment:

```bash
export IAM_TOKEN=your_token
```

### Modes

- users: create users, folders, access; stream output CSV
- ydb: create VPC+subnets (if needed) and YDB databases; supports targeting folders
- reset-password: reset user passwords; stream output CSV
- generate-load: generate ydb CLI load scripts for existing YDB databases

Common flags:
- `--cloud-id <id>`: Cloud ID
- `--created-users-file <path>`: CSV output (users and reset-password modes)

#### users
```bash
python main.py --do users \
  --userpool-id <pool_id> \
  --num-users <1..100> \
  --domain <domain> \
  --cloud-id <cloud_id> \
  --created-users-file created_users.csv
```

#### ydb
```bash
# All folders (except skips)
python main.py --do ydb --cloud-id <cloud_id> \
  --skip-folder-ids folderA,folderB

# Only specified folders
python main.py --do ydb --cloud-id <cloud_id> \
  --create-ydb-in-folders folderX,folderY
```

Behavior:
- Reuses existing VPC with subnets across required zones; otherwise creates one
- Skips folder if a YDB with storageConfig.storageOptions groupCount>1 exists

#### reset-password
```bash
# Specific users
python main.py --do reset-password --userpool-id <pool_id> \
  --user-ids user1,user2 --created-users-file reset_results.csv

# All users in userpool
python main.py --do reset-password --userpool-id <pool_id> \
  --created-users-file reset_results.csv
```

#### generate-load
```bash
python main.py --do generate-load --cloud-id <cloud_id> \
  --folder-ids folderA,folderB \
  --skip-folder-ids folderC \
  --batch-size 16 \
  --output-dir ./scripts
```
Outputs two executable scripts in output-dir:
- `init.bash`: ydb workload kv init commands
- `run-mixed-and-select.bash`: ydb workload kv mixed and select commands

### Sample Output

```
2024-01-15 10:30:15,123 - INFO - Starting user creation: 3 users in pool myuserpool
2024-01-15 10:30:15,456 - INFO - Password generated successfully
2024-01-15 10:30:16,789 - INFO - User creation request submitted for aragornbaggins@example.com
2024-01-15 10:30:16,790 - INFO - Created user 1/3: aragornbaggins@example.com (Aragorn Baggins)
2024-01-15 10:30:17,123 - INFO - Password generated successfully
2024-01-15 10:30:18,456 - INFO - User creation request submitted for pierrebezukhov@example.com
2024-01-15 10:30:18,457 - INFO - Created user 2/3: pierrebezukhov@example.com (Pierre Bezukhov)
2024-01-15 10:30:19,789 - INFO - Password generated successfully
2024-01-15 10:30:21,012 - INFO - User creation request submitted for frodotook@example.com
2024-01-15 10:30:21,013 - INFO - Created user 3/3: frodotook@example.com (Frodo Took)
2024-01-15 10:30:21,014 - INFO - User creation completed. Successfully created 3 users
2024-01-15 10:30:21,015 - INFO - ✓ aragornbaggins@example.com - Aragorn Baggins
2024-01-15 10:30:21,016 - INFO - ✓ pierrebezukhov@example.com - Pierre Bezukhov
2024-01-15 10:30:21,017 - INFO - ✓ frodotook@example.com - Frodo Took
```

## Name Generation

The tool generates unique names from:
- **Lord of the Rings characters**: Aragorn, Gandalf, Frodo, Samwise, etc.
- **War and Peace characters**: Pierre, Andrei, Natasha, Marya, etc.

Names are combined to create unique first and last name combinations within each session.

## Error Handling

The tool includes comprehensive error handling for:
- Invalid parameters
- Network connectivity issues
- API authentication errors
- User creation failures

## Troubleshooting

### Common Issues

1. **"IAM_TOKEN environment variable is required"**
   - Make sure you've set the `IAM_TOKEN` environment variable
   - Verify the token is valid and has appropriate permissions

2. **"Validation error"**
   - Check that userpool-id contains only letters and digits
   - Ensure num-users is between 1 and 100
   - Verify domain name syntax is correct

3. **"User creation failed"**
   - Check your internet connection
   - Verify your IAM token has permission to create users
   - Ensure the user pool ID exists in your Yandex Cloud account

### Getting Help

Run the tool with `--help` to see all available options:

```bash
python main.py --help
```

## API Endpoints Used (selection)

- Password Generation: `POST .../v1/idp/users:generatePassword`
- User Creation: `POST .../v1/idp/users`
- Folder Creation: `POST https://resource-manager.api.cloud.yandex.net/resource-manager/v1/folders`
- Folder Access: `POST .../v1/folders/{id}:setAccessBindings`
- Cloud Access Update: `POST .../v1/clouds/{id}:updateAccessBindings`
- VPC Networks/Subnets: `POST https://vpc.api.cloud.yandex.net/vpc/v1/networks`, `POST .../v1/subnets`
- YDB Create/List: `POST https://ydb.api.cloud.yandex.net/ydb/v1/databases`, `GET .../v1/databases`

## Security Notes

- The IAM token is passed in the Authorization header as `Bearer <token>`
- Generated passwords are created using Yandex Cloud's secure password generation API
- All API communications use HTTPS
- Never commit your IAM token to version control
