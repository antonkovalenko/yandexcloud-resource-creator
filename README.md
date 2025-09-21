# Yandex Cloud User Creation CLI Tool

A Python CLI tool for creating users in Yandex Cloud using the organization-manager API.

## Features

- Create multiple users in Yandex Cloud with a single command
- Generate unique names from Lord of the Rings and War and Peace characters
- Automatic password generation via Yandex Cloud API
- Comprehensive parameter validation
- Detailed logging to stdout

## Prerequisites

- Python 3.7 or higher
- Yandex Cloud IAM token with appropriate permissions
- Access to Yandex Cloud organization-manager API

## Installation

### 1. Clone or download the project

```bash
# If using git
git clone <repository-url>
cd neuroscale-2025

# Or simply navigate to the project directory if you have the files
cd /path/to/neuroscale-2025
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

### Basic Command

```bash
python main.py --userpool-id <pool_id> --num-users <number> --domain <domain>
```

### Parameters

- `--userpool-id`: User pool ID (required)
  - Must be a string of letters and digits
  - Cannot be empty
  - Cannot be longer than 32 characters

- `--num-users`: Number of users to create (required)
  - Must be between 1 and 100
  - Cannot be zero

- `--domain`: Domain name for user emails (required)
  - Must be a valid internet domain syntax

### Examples

```bash
# Create 5 users in userpool "myuserpool" with domain "example.com"
python main.py --userpool-id myuserpool --num-users 5 --domain example.com

# Create 10 users in userpool "test123" with domain "company.org"
python main.py --userpool-id test123 --num-users 10 --domain company.org
```

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

## API Endpoints Used

- **Password Generation**: `POST https://organization-manager.api.cloud.yandex.net/organization-manager/v1/idp/users:generatePassword`
- **User Creation**: `POST https://organization-manager.api.cloud.yandex.net/organization-manager/v1/idp/users`

## Security Notes

- The IAM token is passed in the Authorization header as `Bearer <token>`
- Generated passwords are created using Yandex Cloud's secure password generation API
- All API communications use HTTPS
- Never commit your IAM token to version control
