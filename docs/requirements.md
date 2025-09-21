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

### Delete users

