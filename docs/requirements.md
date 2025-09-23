## Non-functional requirements

1. Resulting program must be a CLI written in python. Main file must by main.py. It should use virtual env and has requirements.txt with list of required modules.
2. It must have README.md with a set of steps to install requirements into virtual env and activate it and run the program
3. Program must have command line options to send parameters
4. Program must use logging to stdout for output


## Authentication


Program must use auth from env variable IAM_TOKEN for authentication.
Specify the IAM token when accessing Yandex Cloud resources via the API. Provide the IAM token in the Authorization header in the following format:

Authorization: Bearer <IAM_token>

## Use cases

### Create users

I want to create users in Yandex Cloud. I want run resulting comannd line program, specify:
- user pool id 
- number of users to create
- domain name to use


Parameters must be validated:

user pool id is a string of letters and digits, can not be longer than 32 cannot be empty or ommitted
number of users can't be zero it is required can't be greater than 100
domain name must be valid syntaxycally as an internet domain

Program must create users using this REST API call

#### URL

POST https://organization-manager.api.cloud.yandex.net/organization-manager/v1/idp/users


#### Body parameters

{
  "userpoolId": "string",
  "username": "string",
  "fullName": "string",
  "givenName": "string",
  "familyName": "string",
  "email": "string",
  "phoneNumber": "string",
  // Includes only one of the fields `passwordSpec`, `passwordHash`
  "passwordSpec": {
    "password": "string",
    "generationProof": "string"
  },
  "passwordHash": {
    "passwordHash": "string",
    "passwordHashType": "string"
  },
  // end of the list of possible fields
  "isActive": "boolean",
  "externalId": "string"
}


#### Response parameters

{
  "id": "string",
  "description": "string",
  "createdAt": "string",
  "createdBy": "string",
  "modifiedAt": "string",
  "done": "boolean",
  "metadata": {
    "userId": "string"
  },
  // Includes only one of the fields `error`, `response`
  "error": {
    "code": "integer",
    "message": "string",
    "details": [
      "object"
    ]
  },
  "response": {
    "id": "string",
    "userpoolId": "string",
    "status": "string",
    "username": "string",
    "fullName": "string",
    "givenName": "string",
    "familyName": "string",
    "email": "string",
    "phoneNumber": "string",
    "createdAt": "string",
    "updatedAt": "string",
    "externalId": "string"
  }
  // end of the list of possible fields
}


#### Last name and first name generation

Generate a last name and a first name for every user. Last and first name combindation must be unique within a generation session. Use list of names and last names of characters from The lord of rings and war and piece be leo tolstoy. They must be in latin letters

#### Username generation

Username must be generated to be no longer than 12 letters and must be human readable. In a form of generated username concatenated with @ sign and domain parameter.

### Password generation

When creating user use password generated via following api call

REST API 

POST https://organization-manager.api.cloud.yandex.net/organization-manager/v1/idp/users:generatePassword

Response will be like

{
  "passwordSpec": {
    "password": "string",
    "generationProof": "string"
  }
}

### Reset passwords

Program must support resetting passwords for users in a userpool.

- If a list of user IDs is provided, reset for those users
- If not provided, list all users in the userpool and reset for each
- For each user:
  - Generate a password via `POST .../v1/idp/users:generatePassword`
  - Call `POST .../v1/idp/users/{userId}:setOthersPassword` and poll the operation until done

Output results (user id, username, password) to CSV as users are processed.

### Create VPC and YDB database

Program must support creating network infrastructure and YDB databases per folder.

- For each folder, first check if a suitable VPC with subnets across required zones exists; reuse if found
- If no such VPC exists, create one network and three subnets (zones: ru-central1-a, ru-central1-b, ru-central1-d)
- Before creating YDB, list existing databases in the folder via `GET https://ydb.api.cloud.yandex.net/ydb/v1/databases`
- If any database has `storageConfig.storageOptions[*].groupCount > 1`, skip creating a new YDB in that folder
- Otherwise, create a YDB dedicated database and poll the operation until done

YDB creation must support:

- Processing only folders passed via command line option
- Skipping folders passed via command line option
- Up to 5 concurrent create operations with regular polling (2s) and retries on transient errors

### Generate load scripts for YDB

Program must generate bash scripts to run kv workload via ydb CLI for existing YDB databases with storage groups.

Inputs:

- cloud-id (required)
- folder-ids (optional, comma-separated)
- skip-folder-ids (optional, comma-separated)
- batch-size (optional, default 16, 1..32)
- output-dir (required, existing writable dir)

Behavior:

- Determine folders from folder-ids or list all folders in the cloud
- Skip folders in skip-folder-ids
- For the first YDB found in a folder with storage groups (groupCount > 0), generate commands:
  - `ydb ... workload kv init ... > init-<db_id> 2>&1 &`
  - `ydb ... workload kv run mixed -t 300 --seconds 3600 > mixed-<db_id> 2>&1 &`
  - `ydb ... workload kv run select --threads 100 --seconds 3600 --rows 100 > mixed-<db_id> 2>&1 &`
- Write init commands to `init.bash`, mixed/select to `run-mixed-and-select.bash`
- Add bash shebang and make scripts executable

