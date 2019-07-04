# TestAPI

TestAPI is a template based automation framework for Rest API.

## Getting Started

Automate Rest API’s in just 2 simple steps.

## Step-1:

Create a single Template consisting or URL, Header and Request.

Example – Inside ‘template’ directory ‘demo.json’ file is created.

```
{
  "${URL}": "http://${VAR;host}/api/v1/create",
  "${HEADER}": "",
  "${REQUEST}" : {
    "name":"${RETURN;AUTOGENERATE;C;9;name}",
    "salary":"${VAR;salary}",
    "age":"${VAR;age}"
    }
}

```
## Step-2:

Create a excel file consisting request and response data and run the program Example – Inside ‘apidata’ folder an excel file with the same name as template i.e., ‘demo.xlsx’ is created with 2 sheets – ‘request’ and ‘response’. 

Example -

```
salary	age
123	23

name	salary	age	id
${VAR;name}	123	23	${RETURNG;VAR;id}

```

## Okay, let’s see the inbuilt tags supported by TestAPI

### ${AUTOGENERATE;C/N/A;Length;VariableName} 

It can be provided in ${REQUEST},  ${URL}, and ${HEADER}.

It must be used 3 extra tags each separated by semi-colon ‘;’ character– 

*C/N/A – C stands for only characters, N for Number, B for Alphanumeric
	
*Length – Length accepts integer value describing length of the value generated
	
*VariableName – It accepts a string which acts as a variable to store the generated value

Example –

```
${AUTOGENERATE;C;9;name}
```

### ${RETURN;VAR;VariableName}
It can be provided in ${REQUEST},  ${URL}, and ${HEADER}.

It must be used with VAR or AUTOGENERATE tags separated by a semi-colon – 

*VariableName – It accepts a string which acts as a variable to store the generated value
	
It can be used in combination with the autogenerate tag as follows – 

```
${RETURN;AUTOGENERATE;C;9;name}
```

### ${VAR;VariableName}

It represents any variable passed from an external data file (.xlsx file), where the tag is replaced by any value from the data sheet.

### ${RETURNG;VariableName}

It is a special tag to be used only in ${RESPONSE}.

It captures the value from response and makes it Global for use in further test cases.

This tag can be used in the response data sheet as shown in STEP-2 above.

## Few Important points

The folder structure should be the same with same names of the folders – template and apidata

For each template file of any name (demo.json in the example), there should be an excel file inside apidata directory with exactly the same name with .xlsx extension.

There should be two sheets in each file – request and response, as shown in Step-2 above.

First row in the excel sheets are always the variable names. Subsequent rows consist of values.

Variable names must be unique in a template and it’s data file.

