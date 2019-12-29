# Self-documenting JSON REST API

This API implementation offers all the required functionality to support specified functionality and data access.

## Basic Terminology

**URI parameters** are baked into the resource path. For example; `/api/company/123/order/90121` has two URI parameters. The ID of the company entity (`123`) and the ID of the order (`90121`).

**Query parameters** are appended to the URI with `?` character and chained with `&` separator. For example; `/api/classifieddata?begin=1541409470&fields=ss00p01,ss00p02` has two query parameters; `begin`, which is an UNIT timestamp in string format and `fields`, which is a string that can be converted into a comma separated list.

**Payload parameters** are located in the HTTP payload (*body*) portion, in a JSON format (as far as this API specification is concerned). Usage of Payload parameters is reserved to data altering actions, such as PUT,PATCH and POST, which need to deliver number of entity attributes. Notable exception is the DELETE HTTP method, which does not need to send entity data and identifies the target for the delete operation through URI parameter (for example; `/api/item/028121/delete`).

**Header parameters** are located in the HTTP header. Aside from path/endpoint, HTTP method and response codes, these parameters have no other putpose in this API specification and are left for HTTP and application purposes (such as session management, XSS prevention and access control mechanisms). 

## There exists two distinct GET requests

First, the more obvious, can be called as **the "fetch" type**. These GET requests identify the entity with an ID and responses return it as one object. Second type can be called **the "search" type**, which can define any number of criteria that result in zero or more matching entities.

The distinction between these is relevant, because "fetch" type entity requests are supposed to be identified by means of *URI parameters* and because search parameters are to be sent as *query parameters*. Also, "fetch" API endpoints do not support search criterias (usually, only a field selector query paramter).

**When "fetch" yields no results, response "404 Not Found" is returned. When "search" type request yields no results, an empty list is returned with code "200 OK".**

### Endpoints are either Entity generic or Identified Entities

While most CRUD (**C**reate, **R**ead, **U**pdate, **D**elete) actions deal with identified entities (`/api/entity/<int:id>`), POST ("create") action cannot. Only the service can give the new entity instance a valid and non-conflicting ID. GET ("read") action can be either to identified entity (making it "fetch" type), or to entity generic (making it a "search" request).

For this reason, identified routes (`/api/entity/<int:id>`) and generic routes (`/api/entity`) are usually defined separately and offer different sets of supported methods.

## REST API Principles

This implementation follows number of principles.

  * Use (singular) nouns in URIs to name resources. (no verbs, no plurals…)
  * All JSON REST API requests must defined header `Content-Type: application/json`.
  * Specific entity access identifies the target through URI parameter(s): `/api/v1/employee/4121/reservation/1412/`.
  * Meta parameters, such as field selector (specifying which fields are returned), are sent
 as query parameters (…`?fields=firstname,lastname&order=asc`)
  * Both GET request types ("fetch" and "search") accept all parameters as query parameters. (GET requests never send JSON payloads).
  * For non-idempotent (state altering) methods (POST,PUT,PATCH), entity data is required to be sent in JSON payload.
  * DELETE method does not use JSON payloads. Entity is identified by URI parameter (`/user/<id>`).
  * Authentication (keys, cookies, tokens, whatever) shall not use any other storage than the HTTP header.
  * When supporting versions, recommended way is to build that into the endpoint URI: (`/api/v2/user`). This allows supporting multiple versions and very simple interface of obsoleted API versions – they simply are not found. No code to write about “wrong version requested”…
  * "Fetch" type requests are served only via URI parametrized endpoints (`/api/v1/employee/<id>`), "search" type requests shall not be accessible through endpoints that have parametrized the identity of the searched entity. (Correct would be; `/api/v1/employee/`).

## HTTP Methods

    GET     search/fetch
    POST    create
    PUT     NOT USED
    PATCH   update
    DELETE  delete

NOTE: Some specifications make the distinction between PUT and PATCH to be that PUT *replaces* the specified entity, while PATCH *updates* the existing entity. This API has no use for such distinction (nor does that distinction make any sense) and therefore PUT method is unused.

## HTTP Responses

This section discusses HTTP responses in general terms. Implementation strives to follow these principles when ever possible. Most important of the response code usages involved signaling if the requested resource is available at all. For resource (endpoint) + method combinations and their logical meaning, following table should be used:

        +-------------+---------+--------+---------+--------+--------+
        | Resource    | POST    | GET    | PUT     | PATCH  | DELETE |
        +-------------+---------+--------+---------+--------+--------+
        | /user       | Create  | Search | 405     | 405    | 405    |
        | /user/<:id> | 405     | Fetch  | Replace | Update | Delete |
        +-------------+---------+--------+---------+--------+--------+

**Reply `405 Method Not Allowed` should be the only 4xx response used to indicate unavailable method + endpoint combinations.**

### HTTP Response Codes Acknowledged by this API

* `200 OK`<br />**Transaction completed as expected.** It is up to each endpoint implementation to document any payloads they might return.
* `202 Accepted`<br />**Asyncronous action accepted/queued.** This is for actions that cannot be completed within HTTP Request/Response transaction and thus cannot have a definite answer. Instead, asyncronous transaction ID is returned and client may query later for its status (which needs its own API endpoint, of course). *Unless the distinction between completed transactions and pending/asyncronous transactions are needed within one API endpoint, it is also recommended that this return code is also replaced with code 200. For example, if an API endpoint exists to receive commands that get executed when the system has time to do them, then a normal process would never expect any other outcome than to queue commands.*
* `400 Bad Request`<br />**Problems in data schema.** Not recoverable by simply correcting values. Examples might include issues such as misnamed/missing keys, incorrect datatypes or malformed JSON for example.
* `401 Unauthorized`<br />**Unauthorized.** All errors including insifficient privileges and errors in trying to authenticate the session/user/access instance.
* `404 Not Found`<br />**Entity not found.** Provided ID or other data do not match any entity in the database. This is specially for ID / Primary Key use because making the distinction between just some incorrect values and incorrect entity identifier is paramount how a client should proceed.
* `405 Method Not Allowed`<br />**Resource + method combination does not exist.**
* `406 Not Acceptable`<br />**Data value error.** Data schema is OK, but values are errornous or cause database constraint violations. Transaction can be attempted again with corrected values.


### GET (entity generic endpoint)

**Action:** Search  
**Payload:** None  
**URI Parameters:** None  
**Query Parameters:** Implementation defined  
**Returns on Success:** Always a `list` of zero to N entities under key `data`.

**Possible Replies**

        Code                    Payload                 Description
        200 OK                  'data': [{},...]        Success. List of objects (0...N) returned.
        400 Bad Request         None                    Data/structure error.
        401 Unauthorized        None                    Access/authorization error.
        405 Method not allowed  None                    Endpoint + method combo not supported.
        406 Not Acceptable      None                    Argument error.

### GET (identified entity endpoint)

**Action:** Fetch Entity  
**Payload:** None  
**URI Parameters:** `<int:id>` (or similar)  
**Query Parameters:** Implementation defined (possibly to limit which entity attributes are retrieved)  
**Returns on Success:** One entity object under key `data`.

**Possible Replies**

        Code                    Payload                 Description
        200 OK                  'data': {}              Success. Object is returned.
        400 Bad Request         None                    Data/structure error.
        401 Unauthorized        None                    Access/authorization error.
        404 Not Found           None                    Entity by ID not found.
        405 Method not allowed  None                    Endpoint + method combo not supported.
        406 Not Acceptable      None                    Argument error.

### POST (entity generic endpoint)

**Action:** Create  
**Payload:** Entity object JSON  
**URI Parameters:** None  
**Query Parameters:** None  
**Returns on Success:** ID / PK of the new entity under key `data`

**Possible Replies**

        Code                    Payload                 Description
        200 OK                  'data': {'id': <int>}   Success. New entity created.
        202 Accepted            'data': {'id': <int>}   Asyncronous action queued.
        400 Bad Request         None                    Data/structure error.
        401 Unauthorized        None                    Access/authorization error.
        405 Method not allowed  None                    Endpoint + method combo not supported.
        406 Not Acceptable      None                    Argument error.

Response code `202` usage should be carefully considered. If one API endpoint accessed with one method, does not return both asyncronous and immediate response "values", code `200` should be used instead.

### PUT (identified entity endpoint)

This API does not use *replace* operations. "405 Method Not Allowed" is returned. Standard CRUD model (**C**reate, **R**ead, **U**pdate, **D**elete) does not need "replace" operation and it would be difficult to imagine what exactly it would be, if not just another update operation.

### PATCH (identified entity endpoint)

**Action:** Update  
**Payload:** Entity object (with only the attributes to be updated)  
**URI Parameters:** `<int:id>` (or similar)  
**Query Parameters:** None  
**Returns on Success:** ID / PK of the updated entity under key `data` 

**Possible Replies**

        Code                    Payload                 Description
        200 OK                  'data': {'id': <int>}   Success. Entity updated.
        400 Bad Request         None                    Data/structure error.
        401 Unauthorized        None                    Access/authorization error.
        404 Not Found           None                    Entity by ID not found.
        405 Method not allowed  None                    Endpoint + method combo not supported.
        406 Not Acceptable      None                    Argument error.


### DELETE (identified entity endpoint)

**Action:** Delete  
**Payload:** None  
**URI parameters:** `<int:id>` (or similar)  
**Query Parameters:** None  
**Returns on Success:** No payload

**Possible Replies**

        Code                    Payload                 Description
        200 OK                  None                    Success.
        401 Unauthorized        None                    Access/authorization error.
        404 Not Found           None                    Entity by ID not found.
        405 Method not allowed  None                    Endpoint + method combo not supported.
        406 Not Acceptable      None                    Foreign key violation, or other reason.


