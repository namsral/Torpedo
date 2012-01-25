Torpedo
=======

Torpedo allows you to schedule HTTP callbacks via a REST API.

Say you need to send out a message at exactly 8:52 am. But your web framework doesn't support scheduling jobs and setting up a message queue is overkill.

1. Run Torpedo:


		torpedo --port 7931 --address 127.0.0.1



2. Implement the message sending in your web framework of choice and schedule it with calling Torpedo. This example uses the curl command:

		curl -i -X POST http://127.0.0.1:7931/api/callbacks/ \
			-d "url=http://example.com/messages/1/send/" \
			-d "eta=2012-01-25T08:52:00Z"


At 8:52 am exactly, the URL "http://example.com/messages/1/send/" will be called.


Install
-------

1. Create a virtual environment and activate it:

		$ virtualenv env
		$ source env/bin/activate

2. Download the source and install:

		$ python setup.py install

Requirements: tornado >= 2.0

Documentation
-------------

**Add callback:**

* Method: POST
* URL: /api/callbacks/
* Data:
	* eta (Estimated Time of Arrival, ISO 8601 UTC datestring, example: 2012-01-25T08:52:00Z)
	* url (HTTP URL to call, method is always GET)
* Response:

		{
			"url":"http://localhost:port/api/callbacks/<id>/",
		}

**Delete callback:**
	
* Method: DELETE
* URL: /api/callbacks/\<id\>/
* Example:
	
		curl -i -X DELETE http://127.0.0.1:7931/api/callbacks/<id>/

* Response: 204 No Data

**List callbacks:**

* Method: GET
* URL: /api/callbacks/
* Example:
	
		curl -i -X GET http://127.0.0.1:7931/api/callbacks/

* Response:
		
		{
			"total": 2,
			"result": [
				{
					"url": "http://example.com/messages/1/send/",
				 	"eta": "2012-01-25T16:29:00Z",
					"uuid": "9dc97726490ac2ec74ef97b209cda6a09638dca3"
				},
				{
					"url": "http://example.com/messages/2/send/",
					"eta": "2012-01-25T16:29:01Z",
					"uuid": "4086e7e694614f2996bace9ee357c72eb012b4da"
				}
		}


FAQ
===

Q: Can I use Torpedo as a job queue?  
A: No, your web framework has to do all the work, Torpedo just triggers your framework to execute the job at the specified time.

Q: Is Torpedo persistent?  
A: No, everything is kept in memory to keep things simple. If Torpedo needs to restart have your web framework reregister all pending callbacks.
